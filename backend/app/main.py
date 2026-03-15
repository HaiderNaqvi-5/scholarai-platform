import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.database import async_session_factory
from app.demo import seed_demo_data_if_enabled
from app.schemas import HealthResponse


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await seed_demo_data_if_enabled()
        yield

    app = FastAPI(
        title=settings.APP_NAME,
        description="ScholarAI modular monolith MVP foundation",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*", "X-Request-ID"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.get("/health", tags=["system"], response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        db_ok = False
        try:
            async with async_session_factory() as db:
                await db.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False

        return HealthResponse(
            status="healthy" if db_ok else "degraded",
            version=settings.APP_VERSION,
            database="ok" if db_ok else "error",
        )

    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()
