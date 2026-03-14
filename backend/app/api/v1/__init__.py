from fastapi import APIRouter

from app.api.v1.routes import admin, ai, applications, auth, profile, scholarships

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(profile.router, prefix="/profile", tags=["Student Profile"])
router.include_router(scholarships.router, prefix="/scholarships", tags=["Scholarships"])
router.include_router(applications.router, prefix="/applications", tags=["Applications"])
router.include_router(admin.router, prefix="/admin", tags=["Admin"])
router.include_router(ai.router, prefix="/ai", tags=["AI Tools"])
