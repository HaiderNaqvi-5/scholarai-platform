import uuid
from typing import Any
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import router as api_v1_router
from app.api.v2 import router as api_v2_router
from app.core.config import settings
from app.core.database import async_session_factory
from app.demo import seed_demo_data_if_enabled
from app.schemas import ErrorDetail, ErrorEnvelope, HealthResponse
from scholarai_common.errors import ScholarAIException


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach OWASP-recommended response headers to every response.

    Values are conservative defaults that work for an API + thin frontend.
    Override per-route via response.headers when a relaxation is necessary.
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        # HTTPS-only enforcement. Browsers honor only when delivered over TLS.
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
        # Clickjacking
        response.headers.setdefault("X-Frame-Options", "DENY")
        # MIME-sniffing
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        # Referrer leak
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        # Cross-origin isolation hints
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        # Permissions API surface — drop everything the API does not use.
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        )
        # API responses are JSON. A strict CSP for the FastAPI surface keeps
        # browsers honest even if /docs swagger is open to the network.
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        return response


def _init_sentry() -> None:
    """Initialise Sentry only when SENTRY_DSN is set.

    Bundled in requirements.txt for the Air-Uni booth; opt-in via env so
    local dev + CI boot clean. Failure to import is fatal (the package is
    a hard dependency); failure to init is logged and ignored so an
    invalid DSN never blocks app boot.
    """
    dsn = getattr(settings, "SENTRY_DSN", None) or None
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=getattr(settings, "SENTRY_ENVIRONMENT", "development"),
            traces_sample_rate=float(getattr(settings, "SENTRY_TRACES_SAMPLE_RATE", 0.0) or 0.0),
            profiles_sample_rate=float(getattr(settings, "SENTRY_PROFILES_SAMPLE_RATE", 0.0) or 0.0),
            integrations=[FastApiIntegration(), StarletteIntegration()],
            send_default_pii=False,
        )
    except Exception as err:  # pragma: no cover — defensive only
        import logging

        logging.getLogger(__name__).warning("Sentry init failed: %s", err)


def create_app() -> FastAPI:
    _init_sentry()

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

    # S7 — Trust X-Forwarded-* when behind a reverse proxy. trusted_hosts
    # filters which upstream IPs are allowed to set the header chain;
    # "*" trusts the host network, which is fine inside the docker compose
    # private network. For prod set behind cloudflare/caddy to "127.0.0.1".
    if settings.TRUSTED_PROXY_HOPS > 0:
        app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

    # Order matters: TrustedHost runs first (rejects bad Host header before
    # any other middleware reads it), CORS next (preflight needs to land
    # before security headers attach), security headers last so every
    # response — including CORS preflight — carries them.
    if settings.ALLOWED_HOSTS:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*", "X-Request-ID"],
    )

    app.add_middleware(SecurityHeadersMiddleware)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        if request.url.path.startswith(settings.API_V1_PREFIX):
            response.headers["X-API-Contract-Version"] = "v1"
        elif request.url.path.startswith(settings.API_V2_PREFIX):
            response.headers["X-API-Contract-Version"] = "v2"

        if settings.API_V1_DEPRECATION_ENABLED and request.url.path.startswith(settings.API_V1_PREFIX):
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = _v1_sunset_header_value(settings.API_V1_DEPRECATION_DAYS)
            response.headers["Link"] = f"<{settings.API_V2_PREFIX}>; rel=\"successor-version\""
            response.headers["X-API-V1-Sunset-Days"] = _v1_sunset_days_remaining(
                settings.API_V1_DEPRECATION_DAYS
            )
        return response

    @app.exception_handler(ScholarAIException)
    async def handle_scholarai_exception(
        request: Request,
        exc: ScholarAIException,
    ) -> JSONResponse:
        return build_error_response(
            request=request,
            status_code=exc.status_code,
            code=exc.code.value,
            message=exc.message,
            details=_normalize_error_details(exc.detail),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        message, details = _extract_http_exception_payload(exc.detail)
        return build_error_response(
            request=request,
            status_code=exc.status_code,
            code=http_error_code(exc.status_code),
            message=message,
            details=details,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else {}
        message = first_error.get("msg", "Request validation failed")
        details = _build_validation_error_details(exc)
        return build_error_response(
            request=request,
            status_code=422,
            code="REQUEST_VALIDATION_ERROR",
            message=message,
            details=details,
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
        # S12 — best-effort Sentry capture. No-op when DSN is unset because
        # the sentry_sdk hub is uninitialised; in that case the import is
        # cheap and the call returns immediately.
        try:
            import sentry_sdk

            sentry_sdk.capture_exception(exc)
        except Exception:  # pragma: no cover — never let telemetry mask the 500
            pass

        return build_error_response(
            request=request,
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="Unexpected server error",
        )

    @app.get("/livez", tags=["system"])
    async def liveness_probe() -> dict[str, str]:
        # Process-liveness only. No I/O, no deps. Container orchestrator HEALTHCHECK target.
        return {"status": "alive"}

    @app.get("/readyz", tags=["system"])
    async def readiness_probe() -> Response:
        # Readiness gate: DB reachable. No analytics. Safe for load-balancer probes.
        try:
            async with async_session_factory() as db:
                await db.execute(text("SELECT 1"))
            return JSONResponse({"status": "ready"}, status_code=200)
        except Exception:
            return JSONResponse({"status": "not_ready"}, status_code=503)

    @app.get("/health", tags=["system"], response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        # S15 — Public probe only. DB reachability + version are safe to
        # leak; KPI alert messages are not (they can reveal recommendation
        # pass-rates / volume signals to attackers). Admins read the full
        # KPI surface via the auth-gated /api/v1/analytics endpoint
        # already wired in the admin shell.
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
            kpi_alerts=[],
        )

    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
    app.include_router(api_v2_router, prefix=settings.API_V2_PREFIX)
    return app


app = create_app()


def build_error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | list[Any] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    payload = ErrorEnvelope(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=request_id,
            status=status_code,
            details=details,
        )
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


def _normalize_error_details(
    detail: Any,
) -> dict[str, Any] | list[Any] | None:
    if detail is None:
        return None
    if isinstance(detail, (dict, list)):
        return detail
    return {"detail": str(detail)}


def _extract_http_exception_payload(
    detail: Any,
) -> tuple[str, dict[str, Any] | list[Any] | None]:
    details = _normalize_error_details(detail)

    if isinstance(detail, str):
        return detail, details

    if isinstance(detail, dict):
        if isinstance(detail.get("message"), str):
            return detail["message"], details
        if isinstance(detail.get("detail"), str):
            return detail["detail"], details

    if isinstance(detail, list):
        return "Request failed", details

    if detail is None:
        return "Request failed", None

    return str(detail), details


def _build_validation_error_details(exc: RequestValidationError) -> dict[str, Any]:
    normalized_errors: list[dict[str, Any]] = []
    for error in exc.errors():
        location = error.get("loc")
        if isinstance(location, tuple):
            location = list(location)
        normalized_errors.append(
            {
                "loc": location,
                "msg": error.get("msg"),
                "type": error.get("type"),
                "input": error.get("input"),
            }
        )

    first = normalized_errors[0] if normalized_errors else {}
    return {
        "field": first.get("loc"),
        "errors": normalized_errors,
    }


def _v1_sunset_header_value(deprecation_days: int) -> str:
    from datetime import timedelta

    sunset_at = (datetime.now(timezone.utc) + timedelta(days=max(deprecation_days, 1))).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    return sunset_at


def _v1_sunset_days_remaining(deprecation_days: int) -> str:
    return str(max(deprecation_days, 1))
