from fastapi import APIRouter

from app.api.v1.routes import analytics, documents, interview, recommendations, scholarships, students

router = APIRouter()

router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations v2"])
router.include_router(documents.router, prefix="/documents", tags=["Documents v2"])
router.include_router(interview.router, prefix="/interviews", tags=["Interview Practice v2"])
router.include_router(students.router, prefix="/profile", tags=["Student Profile v2"])
router.include_router(scholarships.router, prefix="/scholarships", tags=["Scholarships v2"])
router.include_router(analytics.router, prefix="/analytics", tags=["Admin Analytics v2"])
