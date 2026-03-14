"""
ScholarAI FastAPI application entry point.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.rate_limit import limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB tables and warm the embedding model if possible."""
    from app.core.database import engine
    from app.models.models import Base

    logger.info("ScholarAI starting - creating DB tables if needed")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        from app.services.recommendation_service import RecommendationService

        RecommendationService._warm_embedding_model()
        logger.info("Embedding model warm-up complete")
    except Exception:
        logger.warning("Embedding model warm-up skipped")

    logger.info("ScholarAI startup complete")
    yield

    logger.info("ScholarAI shutting down - closing DB pool")
    await engine.dispose()


app = FastAPI(
    title="ScholarAI API",
    description="AI-powered scholarship discovery and recommendation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Request-ID"],
)
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health_check():
    """Liveness probe that returns DB connectivity status."""
    from sqlalchemy import text

    from app.core.database import async_session_factory

    db_ok = False
    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "healthy" if db_ok else "degraded",
        "version": "1.0.0",
        "database": "ok" if db_ok else "error",
    }
