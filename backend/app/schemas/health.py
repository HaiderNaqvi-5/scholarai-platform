from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    request_id: str | None = None
    status: int


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail
