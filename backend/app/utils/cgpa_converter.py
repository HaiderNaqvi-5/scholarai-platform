"""Pakistani CGPA conversion utilities (Feature 2, PRD §2).

Pakistani universities use a 4.0 scale nominally, but grade distributions
differ from US universities. These functions translate a Pakistani CGPA to:
- US GPA equivalent for matching against US/Canadian graduate programs.
- UK degree classification for matching against UK MS/PhD programs.

Outputs are deliberately discrete tiers (not linear) so explanation copy
reads as a clean assertion rather than a spurious continuous value.
"""

from __future__ import annotations


_US_GPA_TIERS = (
    (3.8, 3.8, "strong"),
    (3.5, 3.5, "competitive"),
    (3.2, 3.2, "acceptable"),
    (3.0, 3.0, "borderline"),
)


_UK_DEGREE_TIERS = (
    (3.7, "First Class Honours"),
    (3.3, "Upper Second (2:1)"),
    (3.0, "Lower Second (2:2)"),
)


def pakistani_to_us_gpa(cgpa: float | None) -> float | None:
    """Return the US GPA equivalent for a Pakistani 4.0-scale CGPA.

    Below 3.0 we return the raw value (no adjustment) — uplift only applies
    where US admissions committees give Pakistani 4.0-scale grades credit
    for stricter distributions.
    """
    if cgpa is None:
        return None
    if cgpa < 0:
        return None
    for threshold, equivalent, _ in _US_GPA_TIERS:
        if cgpa >= threshold:
            return equivalent
    return float(round(cgpa, 2))


def pakistani_to_us_gpa_tier(cgpa: float | None) -> str | None:
    """Return the human-readable tier label (strong/competitive/...)."""
    if cgpa is None:
        return None
    for threshold, _, label in _US_GPA_TIERS:
        if cgpa >= threshold:
            return label
    return "below_minimum"


def pakistani_to_uk_class(cgpa: float | None) -> str | None:
    """Return UK degree classification equivalent."""
    if cgpa is None:
        return None
    for threshold, label in _UK_DEGREE_TIERS:
        if cgpa >= threshold:
            return label
    return "Third Class"


def cgpa_explanation_note(
    cgpa: float | None,
    pakistani_university: str | None = None,
) -> str | None:
    """Return a one-line explanation string for the recommendation panel.

    Example: "Your 3.6 CGPA from NUST is equivalent to a 3.5 US GPA."
    """
    if cgpa is None:
        return None
    us_equivalent = pakistani_to_us_gpa(cgpa)
    if us_equivalent is None:
        return None
    origin = f" from {pakistani_university}" if pakistani_university else ""
    return (
        f"Your {cgpa:g} CGPA{origin} is equivalent to a "
        f"{us_equivalent:g} US GPA for admission purposes."
    )
