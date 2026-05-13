"""Compute a 0-100 lead score for a Pakistani student profile.

Used by the B2B pipeline to prioritise university outreach. Has zero
imports from any matching code so the recommendation engine stays
trust-boundary-pure (PRD §0.6 rule 1).
"""

from __future__ import annotations

from app.models import StudentProfile


def compute_lead_score(profile: StudentProfile | None) -> int:
    if profile is None:
        return 0
    score = 0

    cgpa = float(profile.gpa_value) if profile.gpa_value is not None else None
    if cgpa is not None:
        if cgpa >= 3.7:
            score += 25
        elif cgpa >= 3.5:
            score += 20
        elif cgpa >= 3.2:
            score += 12
        elif cgpa >= 3.0:
            score += 6

    if profile.ielts_score is not None and float(profile.ielts_score) >= 7.0:
        score += 15
    elif profile.ielts_score is not None and float(profile.ielts_score) >= 6.5:
        score += 10
    elif profile.toefl_score is not None and int(profile.toefl_score) >= 95:
        score += 12

    if profile.funding_requirement in {"fully_funded_only", "partial_ok"}:
        score += 10

    if profile.pakistani_university:
        score += 5
    if profile.degree_subject:
        score += 5
    if profile.graduation_year:
        score += 4
    if profile.city_of_origin:
        score += 2
    if profile.linkedin_url:
        score += 4
    if profile.github_url:
        score += 4
    if profile.research_publication_count and profile.research_publication_count > 0:
        score += 6

    if profile.years_work_experience and profile.years_work_experience >= 1:
        score += 8
    if profile.target_fields:
        score += min(6, 2 * len(profile.target_fields))
    if profile.target_countries:
        score += min(6, 2 * len(profile.target_countries))

    return max(0, min(100, score))
