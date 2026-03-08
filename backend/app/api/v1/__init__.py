from fastapi import APIRouter

from app.api.v1.routes import auth, profile, scholarships, credentials, interview, mentorship, sop, admin

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(profile.router, prefix="/profile", tags=["Student Profile"])
router.include_router(scholarships.router, prefix="/scholarships", tags=["Scholarships"])
router.include_router(credentials.router, prefix="/credentials", tags=["Credentials"])
router.include_router(interview.router, prefix="/interview", tags=["Interview Simulator"])
router.include_router(mentorship.router, prefix="/mentorship", tags=["Mentorship"])
router.include_router(sop.router, prefix="/sop", tags=["SOP Assistant"])
router.include_router(admin.router, prefix="/admin", tags=["Admin"])
