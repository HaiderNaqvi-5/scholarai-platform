"""
ScholarAI FastAPI application entry point.

Features:
  - Async lifespan (DB, embedding model warm-up)
  - CORS middleware
  - Request-ID middleware for distributed tracing
  - Structured logging
  - /health endpoint with DB check
"""
from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import router as api_v1_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB tables + warm embedding model. Shutdown: close pool."""
    from app.core.database import engine
    from app.models.models import Base

    logger.info("ScholarAI starting — creating DB tables if needed...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Warm up the embedding model in the background (non-blocking)
    try:
        from app.services.recommendation_service import RecommendationService
        RecommendationService._warm_embedding_model()
        logger.info("Embedding model warm-up complete")
    except Exception:
        logger.warning("Embedding model warm-up skipped — install sentence-transformers")

    logger.info("ScholarAI startup complete ✓")
    yield

    logger.info("ScholarAI shutting down — closing DB pool")
    await engine.dispose()


app = FastAPI(
    title="ScholarAI API",
    description="AI-powered scholarship discovery and recommendation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Request-ID"],
)


# ── Request-ID middleware (adds X-Request-ID to every response) ───────────────

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(api_v1_router, prefix="/api/v1")


# ── System endpoints ──────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health_check():
    """Liveness probe — returns DB connectivity status."""
    from app.core.database import async_session_factory
    from sqlalchemy import text

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
