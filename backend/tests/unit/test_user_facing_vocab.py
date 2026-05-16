"""Q1 retier vocab guard: internal classification tokens must not leak to user surfaces.

Forbidden tokens (whole-word, case-insensitive): eligible, partial, stretch,
premium, standard, bucket, tier. Three scan targets:
1. _build_tiers pricing bullets (every currency).
2. A synthesized MatchResponse JSON payload.
3. Frontend src .tsx / .ts user-visible string literals.
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Iterable

import pytest

FORBIDDEN: frozenset[str] = frozenset(
    {"eligible", "partial", "stretch", "premium", "standard", "bucket", "tier"}
)
_PATTERN = re.compile(
    rf"\b({'|'.join(re.escape(t) for t in FORBIDDEN)})\b", re.IGNORECASE
)


def _scan(text: str) -> list[str]:
    return [m.group(0).lower() for m in _PATTERN.finditer(text)]


@pytest.mark.parametrize("currency", ["PKR", "GBP", "EUR", "AED", "USD"])
def test_no_internal_vocab_in_pricing_bullets(currency: str) -> None:
    from app.api.v1.routes.waitlist import _build_tiers

    for tier in _build_tiers(currency):
        joined = "\n".join(
            [
                tier.feature_summary or "",
                *(tier.bullet_features or []),
                tier.label or "",
                tier.monthly_price or "",
                tier.yearly_hint or "",
            ]
        )
        hits = _scan(joined)
        assert not hits, f"forbidden tokens in {tier.key} ({currency}): {hits}"


def test_no_internal_vocab_in_serialized_match_response() -> None:
    from app.schemas.scholarships_match import (
        MatchResponse,
        ScholarshipMatchOut,
        UnlockOffer,
    )

    sample = MatchResponse(
        items=[
            ScholarshipMatchOut(
                id=uuid.uuid4(),
                name="Test Award",
                provider="Test Provider",
                country_code="PK",
                funding_amount="PKR 1,000,000",
                deadline=None,
                compatibility=0.7,
                locked=False,
            ),
            ScholarshipMatchOut(
                id=None,
                name="Reveal with upgrade",
                provider="Reveal with upgrade",
                country_code="PK",
                funding_amount=None,
                deadline=None,
                compatibility=0.91,
                locked=True,
            ),
        ],
        unlock_offer=UnlockOffer(
            to_plan="elite",
            locked_count=2,
            headline="2 matches reserved",
            message="Upgrade to Elite to reveal matches personalised to your profile.",
        ),
    )
    blob = sample.model_dump_json()
    hits = _scan(blob)
    assert not hits, f"forbidden tokens in serialized match response: {hits}\nblob={blob}"


def _iter_frontend_offenders(roots: Iterable[Path]) -> list[str]:
    offenders: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in [*root.rglob("*.tsx"), *root.rglob("*.ts")]:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(text.splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith(("//", "/*", "*")):
                    continue
                low = stripped.lower()
                if low.startswith(("import ", "export type ", "type ", "interface ")):
                    continue
                for m in _PATTERN.finditer(line):
                    token = m.group(0)
                    start, end = m.span()
                    left = line[:start]
                    quote_count = sum(left.count(q) for q in ("'", '"', "`"))
                    in_string = (quote_count % 2) == 1
                    if not in_string and ">" in left and "<" in line[end:]:
                        in_string = True
                    if not in_string:
                        continue
                    offenders.append(f"{path}:{i}: {token}")
    return offenders


@pytest.mark.xfail(strict=False, reason="Frontend cleanup pending in Task 15")
def test_no_internal_vocab_in_frontend_user_strings() -> None:
    root = Path(__file__).resolve().parents[3] / "frontend" / "src"
    assert root.exists(), f"frontend src not found at {root}"
    offenders = _iter_frontend_offenders([root])
    assert not offenders, "forbidden tokens in user-visible strings:\n" + "\n".join(
        offenders
    )
