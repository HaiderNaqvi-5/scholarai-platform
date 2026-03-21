from fastapi import APIRouter

from app.api.v1.routes import recommendations

router = APIRouter()

router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations v2"])
