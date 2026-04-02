from fastapi import APIRouter

from app.api.v1.routes import (
    access_control,
    analytics,
    auth,
    curation,
    documents,
    health,
    interview,
    mentor,
    recommendations,
    saved_opportunities,
    scholarships,
    students,
)

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["System Health"])
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# Canonical profile route used by the frontend.
router.include_router(students.router, prefix="/profile", tags=["Student Profile"])
# Backward-compatible alias for older clients.
router.include_router(students.router, prefix="/profiles", tags=["Student Profile"])
router.include_router(scholarships.router, prefix="/scholarships", tags=["Scholarships"])
router.include_router(
    saved_opportunities.router,
    prefix="/saved-opportunities",
    tags=["Saved Opportunities"],
)
router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(interview.router, prefix="/interviews", tags=["Interview Practice"])
router.include_router(curation.router, prefix="/curation", tags=["Curation"])
# Canonical mentor route used by the frontend.
router.include_router(mentor.router, prefix="/mentor", tags=["Mentor Dashboard"])
# Backward-compatible alias for older clients.
router.include_router(mentor.router, prefix="/mentors", tags=["Mentor Dashboard"])
router.include_router(analytics.router, prefix="/analytics", tags=["Admin Analytics"])
router.include_router(
    access_control.router,
    prefix="/access-control",
    tags=["Access Control"],
)
