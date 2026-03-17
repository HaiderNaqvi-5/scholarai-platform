import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exceptions import SQLAlchemyError

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.database import async_session_factory
from app.demo import seed_demo_data_if_enabled
from app.schemas import ErrorEnvelope, HealthResponse


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
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        return build_error_response(
            request=request,
            status_code=exc.status_code,
            code=http_error_code(exc.status_code),
            message=str(exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else {}
        message = first_error.get("msg", "Request validation failed")
        return build_error_response(
            request=request,
            status_code=422,
            code="REQUEST_VALIDATION_ERROR",
            message=message,
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_exception(
        request: Request,
        exc: SQLAlchemyError,
    ) -> JSONResponse:
        return build_error_response(
            request=request,
            status_code=503,
            code="DATABASE_ERROR",
            message="Database availability issue. Please retry shortly.",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return build_error_response(
            request=request,
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="Unexpected server error",
        )

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


def build_error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    payload = ErrorEnvelope(
        error={
            "code": code,
            "message": message,
            "request_id": request_id,
            "status": status_code,
        }
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def http_error_code(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "REQUEST_VALIDATION_ERROR",
    }
    return mapping.get(status_code, "HTTP_ERROR")
