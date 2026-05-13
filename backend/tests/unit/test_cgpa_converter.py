import pytest

from app.utils.cgpa_converter import (
    cgpa_explanation_note,
    pakistani_to_uk_class,
    pakistani_to_us_gpa,
    pakistani_to_us_gpa_tier,
)


@pytest.mark.parametrize(
    "cgpa,expected",
    [
        (4.0, 3.8),
        (3.9, 3.8),
        (3.8, 3.8),
        (3.7, 3.5),
        (3.5, 3.5),
        (3.4, 3.2),
        (3.2, 3.2),
        (3.1, 3.0),
        (3.0, 3.0),
        (2.9, 2.9),
        (2.5, 2.5),
    ],
)
def test_pakistani_to_us_gpa_tiered(cgpa: float, expected: float) -> None:
    assert pakistani_to_us_gpa(cgpa) == pytest.approx(expected)


def test_pakistani_to_us_gpa_passes_none() -> None:
    assert pakistani_to_us_gpa(None) is None


def test_pakistani_to_us_gpa_negative_returns_none() -> None:
    assert pakistani_to_us_gpa(-1.0) is None


@pytest.mark.parametrize(
    "cgpa,tier",
    [
        (3.85, "strong"),
        (3.6, "competitive"),
        (3.3, "acceptable"),
        (3.05, "borderline"),
        (2.95, "below_minimum"),
    ],
)
def test_pakistani_to_us_gpa_tier_label(cgpa: float, tier: str) -> None:
    assert pakistani_to_us_gpa_tier(cgpa) == tier


@pytest.mark.parametrize(
    "cgpa,uk_class",
    [
        (3.9, "First Class Honours"),
        (3.7, "First Class Honours"),
        (3.5, "Upper Second (2:1)"),
        (3.3, "Upper Second (2:1)"),
        (3.1, "Lower Second (2:2)"),
        (3.0, "Lower Second (2:2)"),
        (2.5, "Third Class"),
    ],
)
def test_pakistani_to_uk_class(cgpa: float, uk_class: str) -> None:
    assert pakistani_to_uk_class(cgpa) == uk_class


def test_explanation_note_includes_university() -> None:
    note = cgpa_explanation_note(3.6, pakistani_university="NUST")
    assert "3.6" in note
    assert "NUST" in note
    assert "3.5 US GPA" in note


def test_explanation_note_without_university() -> None:
    note = cgpa_explanation_note(3.8)
    assert "from" not in note
    assert "3.8" in note
