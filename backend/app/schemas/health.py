from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class KpiAlertItem(BaseModel):
    """One degraded-pass-rate alert surfaced through /health.

    Severity is always ``"warn"`` today — the snapshot service only fires
    one tier of alert. ``"info"`` / ``"critical"`` are reserved for future
    promotion (e.g. pass-rate below a second, harder threshold) without a
    schema break.
    """

    domain: str
    severity: Literal["info", "warn", "critical"]
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    kpi_alerts: list[KpiAlertItem] = Field(default_factory=list)


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    request_id: str | None = None
    status: int
    details: dict[str, Any] | list[Any] | None = None


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail
