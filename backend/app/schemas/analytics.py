"""Pydantic schemas for admin analytics dashboard."""
from pydantic import BaseModel, ConfigDict, Field


class PlatformAnalyticsResponse(BaseModel):
    """Aggregate platform metrics returned to the admin dashboard."""
    model_config = ConfigDict(extra="forbid")

    total_users: int = Field(ge=0)
    student_count: int = Field(ge=0)
    mentor_count: int = Field(ge=0)
    admin_count: int = Field(ge=0)
    total_scholarships: int = Field(ge=0)
    total_applications: int = Field(ge=0)
    submitted_applications: int = Field(ge=0)
    total_documents: int = Field(ge=0)
    total_interview_sessions: int = Field(ge=0)
    ingestion_runs_total: int = Field(ge=0)
    ingestion_runs_failed: int = Field(ge=0)
    kpi_trends: list["KPISnapshotTrendItem"] = Field(default_factory=list)


class KPISnapshotTrendItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_domain: str
    policy_version: str
    total_snapshots: int = Field(ge=0)
    passed_snapshots: int = Field(ge=0)
    failed_snapshots: int = Field(ge=0)
    pass_rate: float = Field(ge=0.0, le=1.0)
