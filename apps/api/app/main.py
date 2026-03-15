from fastapi import FastAPI

from app.api.v1.router import router as api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="ScholarAI API scaffold",
)
app.include_router(api_router, prefix=settings.api_v1_prefix)
