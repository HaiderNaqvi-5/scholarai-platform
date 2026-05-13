"""POST /api/v1/scholarships/match service (Feature 5, PRD §5).

Classifies published scholarships against a Pakistani student profile into
three buckets: eligible / partially_eligible / stretch.

Free-tier users see the first three eligible matches in full; everything
after that is returned in a locked list with minimal fields so the
frontend can blur it and surface an upgrade prompt.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_guard import (
    PRICE_BY_CURRENCY,
    get_price_for_currency,
    has_plan_at_least,
)
from app.models import RecordState, Scholarship, StudentProfile, User
from app.schemas.scholarships_match import (
    LockedScholarshipCard,
    ScholarshipMatchCard,
    ScholarshipMatchRequest,
    ScholarshipMatchResponse,
    UpgradePromptPayload,
)


_FREE_VISIBLE_LIMIT = 3
_STRETCH_CGPA_TOLERANCE = 0.2


class ScholarshipMatchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def match(
        self,
        user: User,
        profile: StudentProfile | None,
        payload: ScholarshipMatchRequest,
    ) -> ScholarshipMatchResponse:
        criteria = self._resolve_criteria(profile, payload)
        scholarships = await self._fetch_published_scholarships()

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

        for bucket in (eligible, partial, stretch):
            bucket.sort(key=_sort_key)

        if has_plan_at_least(user, "elite", "institution"):
            for card in (*eligible, *partial, *stretch):
                card.priority_alert_eligible = bool(
                    card.deadline_days is not None and card.deadline_days <= 7
                )

        total_found = len(eligible) + len(partial) + len(stretch)
        fully_funded_count = sum(
            1
            for c in (*eligible, *partial, *stretch)
            if (c.funding_type or "").lower() in {"full", "fully_funded", "gta_gra"}
        )

        visible_limit = total_found
        locked: list[LockedScholarshipCard] = []
        upgrade_prompt: UpgradePromptPayload | None = None
        if not has_plan_at_least(user, "pro", "elite", "institution"):
            visible_limit = _FREE_VISIBLE_LIMIT
            kept, overflow = _split_after_limit(eligible, _FREE_VISIBLE_LIMIT)
            eligible = kept
            # Demote all partial + stretch + overflow eligible to locked rows.
            for card in (*overflow, *partial, *stretch):
                locked.append(
                    LockedScholarshipCard(
                        scholarship_id=card.scholarship_id,
                        title=card.title,
                        country_code=card.country_code,
                        funding_type=card.funding_type,
                        deadline_days=card.deadline_days,
                    )
                )
            partial = []
            stretch = []

            price = get_price_for_currency(user.plan_currency)
            locked_count = len(locked)
            locked_fully_funded = sum(
                1 for c in locked if (c.funding_type or "").lower() in {"full", "fully_funded", "gta_gra"}
            )
            if locked_count:
                upgrade_prompt = UpgradePromptPayload(
                    required_plan=["pro", "elite", "institution"],
                    price=price,
                    message=(
                        f"{locked_count} more matches including {locked_fully_funded} "
                        f"fully funded — unlock with Pro ({price})."
                    ),
                )

        return ScholarshipMatchResponse(
            eligible=eligible,
            partially_eligible=partial,
            stretch=stretch,
            locked=locked,
            total_found=total_found,
            fully_funded_count=fully_funded_count,
            visible_limit=visible_limit,
            upgrade_prompt=upgrade_prompt,
        )

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

    async def _fetch_published_scholarships(self) -> list[Scholarship]:
        result = await self.db.execute(
            select(Scholarship).where(Scholarship.record_state == RecordState.PUBLISHED)
        )
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
        if funding_pref == "fully_funded_only" and scholarship_funding not in {
            "full",
            "fully_funded",
            "gta_gra",
        }:
            # Demote to stretch rather than exclude — students often relax funding pref.
            funding_demotion = True
        else:
            funding_demotion = False

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
        if scholarship_funding in {"full", "fully_funded", "gta_gra"}:
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
        if scholarship_funding in {"full", "fully_funded", "gta_gra"}:
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
