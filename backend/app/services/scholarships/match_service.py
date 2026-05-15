"""POST /api/v1/scholarships/match service (Feature 5, PRD §5).

Internal classification (eligible / partial / stretch) drives sort order
but never leaks to the public API surface. The public response — see
``app.schemas.scholarships_match.MatchResponse`` — exposes only neutral
fields (id, name, provider, country_code, funding_amount, deadline,
compatibility, locked) plus an optional ``UnlockOffer``.

Per-plan policy (Q1 retier, Task 7):
- free: returns up to MATCH_CAP["free"] rows from the bottom bucket only,
  and offers a Pro upgrade.
- pro: returns up to MATCH_CAP["pro"] rows; the first
  PRO_BLURRED_BEST_FIT_COUNT bottom-bucket rows render as locked
  placeholders, with an Elite upgrade offer.
- elite / institution: full reveal, no upgrade offer.

A separate internal method ``match_internal`` returns the legacy rich
shape (still typed as ``ScholarshipMatchResponse`` -> compat alias) for
callers that need bucket-level access (e.g. the Elite strategy report).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_guard import (
    MATCH_CAP,
    PRO_BLURRED_BEST_FIT_COUNT,
    PRICE_BY_CURRENCY,
    can_reveal_best_fit,
    can_see_premium,
    get_price_for_currency,
    has_plan_at_least,
)
from app.models import (
    RecordState,
    Scholarship,
    ScholarshipTier,
    StudentProfile,
    User,
)
from app.schemas.scholarships_match import (
    LockedScholarshipCard,
    MatchResponse,
    ScholarshipMatchCard,
    ScholarshipMatchOut,
    ScholarshipMatchRequest,
    UnlockOffer,
    UpgradePromptPayload,
)


_FREE_VISIBLE_LIMIT = 3
_STRETCH_CGPA_TOLERANCE = 0.2

# Placeholder copy for locked rows. Kept neutral — no bucket/tier words.
_LOCKED_PLACEHOLDER = "Reveal with upgrade"


# Funding-type tokens that count as "fully funded". Re-exported from
# app.services.scholarships.__init__ so other services (reports, alerts,
# tracker dashboards) consume one canonical set.
FULLY_FUNDED_TYPES: frozenset[str] = frozenset({"full", "fully_funded", "gta_gra"})


def is_fully_funded(funding_type: str | None) -> bool:
    return (funding_type or "").lower() in FULLY_FUNDED_TYPES


class ScholarshipMatchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def match(
        self,
        user: User,
        profile: StudentProfile | None,
        payload: ScholarshipMatchRequest,
        *,
        top_n: int | None = None,
    ) -> MatchResponse:
        """Public match endpoint.

        Returns a neutral ``MatchResponse`` — no internal vocabulary leaks.

        ``top_n`` is an internal cap used by callers that need only the top
        few matches before plan policy applies. It is applied to the merged
        pre-policy pool, NOT to individual buckets, so callers consistently
        get the highest-scoring rows across the whole pool. The route
        caller passes None.
        """
        bundle = await self._classify_and_sort(user, profile, payload)
        merged = _flatten_buckets(bundle)
        if top_n is not None:
            merged = merged[:top_n]
            # Rebuild bundle from the truncated merge so policy still has
            # per-bucket knowledge.
            bundle = _split_back_into_buckets(merged)

        plan = (user.plan or "free").lower()
        items: list[ScholarshipMatchOut]
        offer: UnlockOffer | None = None

        if plan == "free":
            # Free sees only the bottom bucket, up to MATCH_CAP["free"].
            cap = MATCH_CAP["free"]
            visible = bundle.stretch[:cap]
            items = [_to_public(card, locked=False) for card in visible]
            # Offer Pro whenever there are any matches at all to upgrade
            # towards — the Pro pool covers all three internal buckets.
            total_pool = len(bundle.eligible) + len(bundle.partial) + len(bundle.stretch)
            if total_pool > len(visible):
                hidden = total_pool - len(visible)
                offer = UnlockOffer(
                    to_plan="pro",
                    locked_count=hidden,
                    headline="More personalised matches available",
                    message="Upgrade to Pro to see your full match list.",
                )
        elif plan == "pro":
            cap = MATCH_CAP["pro"]
            pool = merged[:cap]
            items, blurred_count = _apply_pro_blur(pool)
            if blurred_count > 0 and not can_reveal_best_fit(user):
                offer = UnlockOffer(
                    to_plan="elite",
                    locked_count=blurred_count,
                    headline=(
                        f"{blurred_count} match{'es' if blurred_count != 1 else ''} reserved"
                    ),
                    message=(
                        "Upgrade to Elite to reveal matches personalised to your profile."
                    ),
                )
        else:
            # Elite / institution — full reveal up to plan cap, no offer.
            cap = MATCH_CAP.get(plan, MATCH_CAP["elite"])
            pool = merged[:cap]
            items = [_to_public(card, locked=False) for _bucket, card in pool]

        return MatchResponse(items=items, unlock_offer=offer)

    async def match_internal(
        self,
        user: User,
        profile: StudentProfile | None,
        payload: ScholarshipMatchRequest,
        *,
        top_n: int | None = None,
    ) -> "_InternalMatchBundle":
        """Bucket-aware result for internal callers (e.g. strategy report).

        Returns the rich, classified buckets unchanged. Never serialise this
        directly to a client — its field names ("eligible", "partial",
        "stretch") would leak internal vocabulary.
        """
        bundle = await self._classify_and_sort(user, profile, payload)
        if top_n is not None:
            merged = _flatten_buckets(bundle)[:top_n]
            bundle = _split_back_into_buckets(merged)
        return bundle

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    async def _classify_and_sort(
        self,
        user: User,
        profile: StudentProfile | None,
        payload: ScholarshipMatchRequest,
    ) -> "_InternalMatchBundle":
        criteria = self._resolve_criteria(profile, payload)
        include_premium = can_see_premium(user)
        scholarships = await self._fetch_published_scholarships(
            include_premium=include_premium
        )

        eligible: list[ScholarshipMatchCard] = []
        partial: list[ScholarshipMatchCard] = []
        stretch: list[ScholarshipMatchCard] = []

        for s in scholarships:
            classification = self._classify(s, criteria)
            if classification is None:
                continue
            bucket, score, reason = classification
            card = _build_card(s, score=score, reason=reason, criteria=criteria)
            if bucket == "eligible":
                eligible.append(card)
            elif bucket == "partial":
                partial.append(card)
            else:
                stretch.append(card)

        for group in (eligible, partial, stretch):
            group.sort(key=_sort_key)

        if has_plan_at_least(user, "elite", "institution"):
            for card in (*eligible, *partial, *stretch):
                card.priority_alert_eligible = bool(
                    card.deadline_days is not None and card.deadline_days <= 7
                )

        return _InternalMatchBundle(eligible=eligible, partial=partial, stretch=stretch)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _resolve_criteria(
        self,
        profile: StudentProfile | None,
        payload: ScholarshipMatchRequest,
    ) -> "MatchCriteria":
        cgpa = payload.cgpa
        if cgpa is None and profile is not None and profile.gpa_value is not None:
            cgpa = float(profile.gpa_value)

        degree_target = (payload.degree_target or "").strip().upper() or None
        if degree_target is None and profile is not None and profile.target_degree_level is not None:
            degree_target = profile.target_degree_level.value.upper()

        countries = [c.upper() for c in payload.countries if c]
        if not countries and profile is not None:
            countries = [c.upper() for c in (profile.target_countries or []) if c]
            if not countries and profile.target_country_code:
                countries = [profile.target_country_code.upper()]

        fields = [f.strip().lower() for f in payload.fields if f]
        if not fields and profile is not None:
            fields = [f.lower() for f in (profile.target_fields or []) if f]
            if not fields and profile.target_field:
                fields = [profile.target_field.lower()]

        ielts_score = payload.ielts_score
        if ielts_score is None and profile is not None and profile.ielts_score is not None:
            ielts_score = float(profile.ielts_score)

        has_ielts = payload.has_ielts
        if has_ielts is None:
            has_ielts = ielts_score is not None

        has_gre = payload.has_gre
        if has_gre is None and profile is not None:
            has_gre = profile.gre_quant is not None or profile.gre_verbal is not None

        funding_requirement = payload.funding_requirement
        if funding_requirement is None and profile is not None:
            funding_requirement = profile.funding_requirement

        nationality = payload.nationality
        if nationality is None and profile is not None and profile.citizenship_country_code:
            nationality = profile.citizenship_country_code.upper()

        return MatchCriteria(
            cgpa=cgpa,
            degree_target=degree_target,
            fields=fields,
            countries=countries,
            has_ielts=bool(has_ielts),
            ielts_score=ielts_score,
            has_gre=bool(has_gre),
            funding_requirement=funding_requirement,
            nationality=(nationality or "").upper(),
        )

    async def _fetch_published_scholarships(
        self, *, include_premium: bool = True
    ) -> list[Scholarship]:
        stmt = select(Scholarship).where(
            Scholarship.record_state == RecordState.PUBLISHED
        )
        if not include_premium:
            # Filter out higher-tier rows at the SQL boundary so they never
            # enter classification for callers who lack the upgraded plan.
            stmt = stmt.where(Scholarship.tier == ScholarshipTier.STANDARD)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _classify(
        self,
        scholarship: Scholarship,
        criteria: "MatchCriteria",
    ) -> tuple[str, int, str] | None:
        # Nationality: open_to_nationalities ↔ citizenship_rules in our schema.
        rules = [r.upper() for r in (scholarship.citizenship_rules or [])]
        if rules and "*" not in rules and criteria.nationality and criteria.nationality not in rules:
            return None

        # Country target (if scholarship is country-tagged and student targets countries)
        if criteria.countries and scholarship.country_code and scholarship.country_code != "ZZ":
            if scholarship.country_code.upper() not in criteria.countries:
                return None

        # Degree target
        degree_levels = {lvl.upper() for lvl in (scholarship.degree_levels or [])}
        if criteria.degree_target and degree_levels and criteria.degree_target not in degree_levels:
            return None

        # Funding requirement preference
        funding_pref = (criteria.funding_requirement or "").lower()
        scholarship_funding = (scholarship.funding_type or "").lower()
        # Demote to stretch rather than exclude — students often relax funding pref.
        funding_demotion = (
            funding_pref == "fully_funded_only"
            and not is_fully_funded(scholarship.funding_type)
        )

        # CGPA hard floor with stretch tolerance
        min_cgpa = float(scholarship.min_gpa_value) if scholarship.min_gpa_value is not None else None
        cgpa_demotion = False
        if min_cgpa is not None and criteria.cgpa is not None:
            if criteria.cgpa < min_cgpa - _STRETCH_CGPA_TOLERANCE:
                return None
            if criteria.cgpa < min_cgpa:
                cgpa_demotion = True

        # IELTS missing → partial
        ielts_partial = False
        tags = {t.lower() for t in (scholarship.field_tags or [])}
        provenance_tags = []
        if scholarship.provenance_payload:
            provenance_tags = [t.lower() for t in scholarship.provenance_payload.get("tags", [])]
        explicit_no_ielts = "no_ielts_required" in tags or "no_ielts_required" in provenance_tags
        if not criteria.has_ielts and not explicit_no_ielts:
            ielts_partial = True

        # GRE: scholarship's tags may say no_gre_required
        explicit_no_gre = "no_gre_required" in tags or "no_gre_required" in provenance_tags
        gre_blocker = False
        if not criteria.has_gre and not explicit_no_gre and scholarship.country_code == "US":
            # Many US opportunities expect GRE unless tagged otherwise — partial.
            gre_blocker = True

        # Score the match
        score = 50
        if criteria.fields and tags & set(criteria.fields):
            score += 15
        if scholarship_funding in FULLY_FUNDED_TYPES:
            score += 20
        if min_cgpa is None or (criteria.cgpa is not None and criteria.cgpa >= (min_cgpa + 0.3)):
            score += 5
        if scholarship.deadline_at is not None:
            days = _days_until(scholarship.deadline_at)
            if days is not None and 14 <= days <= 120:
                score += 5

        reason_bits: list[str] = []
        if degree_levels and criteria.degree_target in degree_levels:
            reason_bits.append(f"degree {criteria.degree_target}")
        if criteria.fields and tags & set(criteria.fields):
            reason_bits.append("matches your fields")
        if min_cgpa is not None and criteria.cgpa is not None and criteria.cgpa >= min_cgpa:
            reason_bits.append(f"CGPA {criteria.cgpa:g} ≥ {min_cgpa:g}")
        if scholarship_funding in FULLY_FUNDED_TYPES:
            reason_bits.append("fully funded")
        reason = "; ".join(reason_bits) or "Matches your profile."

        if cgpa_demotion or funding_demotion:
            return "stretch", score, reason
        if ielts_partial or gre_blocker:
            return "partial", score, reason
        return "eligible", score, reason


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


from dataclasses import dataclass  # noqa: E402


@dataclass
class MatchCriteria:
    cgpa: float | None
    degree_target: str | None
    fields: list[str]
    countries: list[str]
    has_ielts: bool
    ielts_score: float | None
    has_gre: bool
    funding_requirement: str | None
    nationality: str


def _days_until(deadline: datetime) -> int | None:
    if deadline is None:
        return None
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    delta = deadline - datetime.now(timezone.utc)
    return delta.days


def _build_card(
    s: Scholarship,
    *,
    score: int,
    reason: str,
    criteria: MatchCriteria,
) -> ScholarshipMatchCard:
    open_to_pakistanis = (
        not s.citizenship_rules
        or "*" in {r.upper() for r in s.citizenship_rules}
        or "PK" in {r.upper() for r in s.citizenship_rules}
    )
    return ScholarshipMatchCard(
        scholarship_id=s.id,
        title=s.title,
        provider_name=s.provider_name,
        country_code=s.country_code,
        deadline_at=s.deadline_at,
        funding_type=s.funding_type,
        funding_amount_min=float(s.funding_amount_min) if s.funding_amount_min is not None else None,
        funding_amount_max=float(s.funding_amount_max) if s.funding_amount_max is not None else None,
        field_tags=list(s.field_tags or []),
        degree_levels=list(s.degree_levels or []),
        citizenship_rules=list(s.citizenship_rules or []),
        min_gpa_value=float(s.min_gpa_value) if s.min_gpa_value is not None else None,
        deadline_days=_days_until(s.deadline_at) if s.deadline_at else None,
        match_score=score,
        match_reason=reason,
        open_to_pakistanis=open_to_pakistanis,
    )


def _sort_key(card: ScholarshipMatchCard) -> tuple:
    # Earliest deadline first (None → far future), then highest funding ceiling,
    # then highest score.
    deadline_key = card.deadline_days if card.deadline_days is not None else 10**6
    funding_ceiling = -(card.funding_amount_max or card.funding_amount_min or 0.0)
    return (deadline_key, funding_ceiling, -card.match_score)


def _split_after_limit(
    cards: list[ScholarshipMatchCard], limit: int
) -> tuple[list[ScholarshipMatchCard], list[ScholarshipMatchCard]]:
    return cards[:limit], cards[limit:]


# ----------------------------------------------------------------------
# Q1 retier (Task 7) — internal bundle + public projection helpers.
#
# The "bucket" tag is internal-only. It is paired with each card via a
# plain tuple while building merged / per-plan pools, then dropped at
# the serialisation boundary by ``_to_public`` so the public surface
# stays neutral (no eligible/partial/stretch/bucket/tier vocabulary).
# ----------------------------------------------------------------------


@dataclass
class _InternalMatchBundle:
    """Internal-only classified result. Never serialise directly."""

    eligible: list[ScholarshipMatchCard]
    partial: list[ScholarshipMatchCard]
    stretch: list[ScholarshipMatchCard]


# Tagged pair: (internal bucket label, card). Used while merging /
# splitting / blurring so the bucket info is available at the policy
# layer without becoming a card attribute.
_TaggedCard = tuple[str, ScholarshipMatchCard]


def _flatten_buckets(bundle: _InternalMatchBundle) -> list[_TaggedCard]:
    """Merge eligible → partial → stretch in that order, preserving the
    per-bucket sort (each bucket is already sorted by ``_sort_key``)."""
    merged: list[_TaggedCard] = []
    for card in bundle.eligible:
        merged.append(("eligible", card))
    for card in bundle.partial:
        merged.append(("partial", card))
    for card in bundle.stretch:
        merged.append(("stretch", card))
    return merged


def _split_back_into_buckets(merged: list[_TaggedCard]) -> _InternalMatchBundle:
    """Inverse of ``_flatten_buckets`` — used after applying a global cap
    so the per-plan policy still has bucket-level knowledge."""
    eligible: list[ScholarshipMatchCard] = []
    partial: list[ScholarshipMatchCard] = []
    stretch: list[ScholarshipMatchCard] = []
    for bucket, card in merged:
        if bucket == "eligible":
            eligible.append(card)
        elif bucket == "partial":
            partial.append(card)
        else:
            stretch.append(card)
    return _InternalMatchBundle(eligible=eligible, partial=partial, stretch=stretch)


def _format_funding_amount(card: ScholarshipMatchCard) -> str | None:
    """Render the funding amount as a neutral display string, or None
    when the card carries no numeric funding figures. Currency is not
    inferred — the raw min/max is shown."""
    lo = card.funding_amount_min
    hi = card.funding_amount_max
    if lo is None and hi is None:
        return None
    if lo is not None and hi is not None and lo != hi:
        return f"{lo:,.0f} - {hi:,.0f}"
    value = hi if hi is not None else lo
    return f"{value:,.0f}"


def _compatibility(card: ScholarshipMatchCard) -> float:
    """Project the internal integer score onto the 0..1 surface used by
    the public API. Internal scores are roughly in the 50..95 band; clamp
    defensively so the schema validator never trips."""
    raw = float(card.match_score) / 100.0
    if raw < 0.0:
        return 0.0
    if raw > 1.0:
        return 1.0
    return raw


def _to_public(card: ScholarshipMatchCard, *, locked: bool) -> ScholarshipMatchOut:
    """Project an internal card to the neutral public row.

    When ``locked=True`` the identifying fields are blanked (id, name,
    provider, funding_amount, deadline) so the frontend can render an
    upgrade placeholder; country_code and compatibility are kept so the
    blurred row still hints at relevance without leaking specifics.
    """
    if locked:
        return ScholarshipMatchOut(
            id=None,
            name=_LOCKED_PLACEHOLDER,
            provider=_LOCKED_PLACEHOLDER,
            country_code=card.country_code,
            funding_amount=None,
            deadline=None,
            compatibility=_compatibility(card),
            locked=True,
        )
    deadline_value: date | None = None
    if card.deadline_at is not None:
        deadline_value = card.deadline_at.date()
    return ScholarshipMatchOut(
        id=card.scholarship_id,
        name=card.title,
        provider=card.provider_name or "",
        country_code=card.country_code,
        funding_amount=_format_funding_amount(card),
        deadline=deadline_value,
        compatibility=_compatibility(card),
        locked=False,
    )


def _apply_pro_blur(
    pool: list[_TaggedCard],
) -> tuple[list[ScholarshipMatchOut], int]:
    """Pro tier projection.

    Locks the first ``PRO_BLURRED_BEST_FIT_COUNT`` rows whose internal
    bucket is ``eligible``; everything else (later eligible rows past the
    blur cap, partial, stretch) renders unlocked. Returns the public
    items list plus the count of blurred rows (so the caller can build
    an UnlockOffer)."""
    items: list[ScholarshipMatchOut] = []
    blurred = 0
    for bucket, card in pool:
        if bucket == "eligible" and blurred < PRO_BLURRED_BEST_FIT_COUNT:
            items.append(_to_public(card, locked=True))
            blurred += 1
        else:
            items.append(_to_public(card, locked=False))
    return items, blurred
