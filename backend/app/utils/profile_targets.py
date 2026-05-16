"""Helpers for reading the target-countries fan-out from a StudentProfile.

The same normalisation lives in three places (scholarship match service,
priority-alerts task, strategy-report service). Centralising the rule prevents
drift if the column shape ever changes (e.g. promotes target_country_code
into target_countries[]).
"""

from __future__ import annotations

from typing import Iterable


def resolve_target_countries(profile) -> list[str]:
    """Return the user's target countries as upper-case ISO-2 codes.

    Honours the multi-select `target_countries` array first; falls back to the
    legacy single-value `target_country_code`. Empty / None values are dropped.
    """
    if profile is None:
        return []
    countries: Iterable[str] = profile.target_countries or []
    out = [c.upper() for c in countries if c]
    if not out:
        legacy = getattr(profile, "target_country_code", None)
        if legacy:
            out = [legacy.upper()]
    return out
