"""Scholarship matching package."""

from app.services.scholarships.match_service import (
    FULLY_FUNDED_TYPES,
    ScholarshipMatchService,
    is_fully_funded,
)


__all__ = ["ScholarshipMatchService", "FULLY_FUNDED_TYPES", "is_fully_funded"]
