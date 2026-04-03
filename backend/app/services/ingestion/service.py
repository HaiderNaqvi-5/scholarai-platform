from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import re
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag
from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import IngestionRun, IngestionRunStatus, Scholarship, SourceRegistry, User, UserRole
from app.schemas.curation import (
    CurationRawImportRequest,
    IngestionRunBulkRetryItem,
    IngestionRunBulkRetryRequest,
    IngestionRunBulkRetryResponse,
    IngestionRunDetail,
    IngestionRunListResponse,
    IngestionRunQueueAssignmentRequest,
    IngestionRunRetryRequest,
    IngestionRunSnapshotResponse,
    IngestionRunStartRequest,
    IngestionRunSummary,
)
from app.services.curation import CurationService

logger = logging.getLogger(__name__)

SCHOLARSHIP_KEYWORDS = (
    "scholarship",
    "award",
    "funding",
    "grant",
    "fellowship",
    "bursary",
)
FIELD_KEYWORD_MAP = {
    "data science": ("data science", "data-science", "data scientist"),
    "artificial intelligence": ("artificial intelligence", "machine learning", " ai "),
    "analytics": ("analytics", "business analytics", "data analytics"),
}
DEGREE_KEYWORDS = (
    ("PhD", ("phd", "doctorate", "doctoral")),
    ("MS", ("master", "masters", "m.sc", "msc", "ms ")),
)
GENERIC_LINK_TEXT = {
    "apply",
    "details",
    "find out more",
    "go",
    "learn more",
    "more",
    "program details",
    "read more",
    "see details",
    "view",
    "view details",
}
CONTEXT_CONTAINERS = ("li", "tr", "article", "section", "div", "td", "p")
TITLE_CANDIDATE_TAGS = ("h1", "h2", "h3", "h4", "strong", "b", "th")
MAX_CONTEXT_TEXT_LENGTH = 1600
MAX_SUMMARY_LENGTH = 350
MAX_CAPTURE_ATTEMPTS = 2
CAPTURE_RETRY_BASE_DELAY_SECONDS = 0.75
MAX_CAPTURED_SNAPSHOT_CHARS = 120_000
DEFAULT_MAX_RECORDS = 5
SYSTEM_ACTOR_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


def retry_async(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception: Exception | None = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2**attempt))
            assert last_exception is not None
            raise last_exception

        return wrapper

    return decorator


class RunMetadata(dict):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, dict):
            for key, value in other.items():
                if self.get(key) != value:
                    return False
            return True
        return super().__eq__(other)


@dataclass
class CaptureResult:
    html: str
    final_url: str
    title: str | None
    capture_mode: str
    metadata: dict[str, Any]


@dataclass
class ParseCandidatesResult:
    candidates: list["ParsedScholarshipCandidate"]
    diagnostics: dict[str, Any]


class ParsedScholarshipCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_key: str = Field(min_length=3, max_length=64)
    source_display_name: str = Field(min_length=3, max_length=255)
    source_base_url: HttpUrl
    source_type: str = Field(max_length=64)
    title: str = Field(min_length=3, max_length=255)
    provider_name: str | None = Field(default=None, max_length=255)
    country_code: str = Field(min_length=2, max_length=2)
    source_url: HttpUrl
    summary: str | None = Field(default=None, max_length=4000)
    funding_summary: str | None = Field(default=None, max_length=2000)
    field_tags: list[str] = Field(default_factory=list)
    degree_levels: list[str] = Field(default_factory=lambda: ["MS"])
    citizenship_rules: list[str] = Field(default_factory=list)
    source_document_ref: str | None = Field(default=None, max_length=255)
    imported_at: datetime | None = None
    source_last_seen_at: datetime | None = None
    review_notes: str | None = Field(default=None, max_length=2000)
    provenance_payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()

    def to_import_request(self) -> CurationRawImportRequest:
        return CurationRawImportRequest(
            source_key=self.source_key,
            source_display_name=self.source_display_name,
            source_base_url=str(self.source_base_url),
            source_type=self.source_type,
            title=self.title,
            provider_name=self.provider_name,
            country_code=self.country_code,
            source_url=str(self.source_url),
            external_source_id=None,
            source_document_ref=self.source_document_ref,
            summary=self.summary,
            funding_summary=self.funding_summary,
            field_tags=self.field_tags,
            degree_levels=self.degree_levels,
            citizenship_rules=self.citizenship_rules,
            min_gpa_value=None,
            deadline_at=None,
            imported_at=self.imported_at,
            source_last_seen_at=self.source_last_seen_at,
            review_notes=self.review_notes,
            provenance_payload=self.provenance_payload,
        )


class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_run(
        self,
        payload: IngestionRunStartRequest,
        actor_user: User | uuid.UUID | None,
    ) -> IngestionRunDetail:
        actor_user_id = self._extract_actor_user_id(actor_user)
        created_run = await self.create_run(payload, actor_user)
        return await self.execute_run(
            uuid.UUID(created_run.run_id),
            actor_user_id=actor_user_id,
            max_records=payload.max_records,
            execution_context={
                "selected_mode": "inline",
                "dispatch_status": "inline",
            },
        )

    async def create_run(
        self,
        payload: IngestionRunStartRequest,
        actor_user: User | uuid.UUID | None,
    ) -> IngestionRunDetail:
        actor_user_id = self._extract_actor_user_id(actor_user)
        full_user: User | None = actor_user if isinstance(actor_user, User) else None
        source = await self._get_or_create_source(payload, full_user)
        run = IngestionRun(
            source_registry=source,
            triggered_by_user_id=actor_user_id,
            status=IngestionRunStatus.QUEUED,
            fetch_url=source.base_url,
        )
        run.run_metadata = self._base_run_metadata(
            source=source,
            payload=payload,
            actor_user_id=actor_user_id,
        )
        self.db.add(run)
        await self.db.flush()
        return self._build_detail(run)

    async def execute_run(
        self,
        run_id: uuid.UUID,
        *,
        actor_user_id: uuid.UUID | None,
        max_records: int | None = None,
        execution_context: dict[str, Any] | None = None,
        persist_running_state: bool = False,
    ) -> IngestionRunDetail:
        run = await self._load_run(run_id)
        selected_max_records = max_records or self._read_requested_max_records(run.run_metadata)
        execution_patch = dict(execution_context or {})
        execution_patch.setdefault("selected_mode", "inline")
        execution_patch.setdefault("dispatch_status", "running")
        execution_patch["max_records"] = selected_max_records

        execution_state = dict((run.run_metadata or {}).get("execution") or {})
        execution_state["attempt_count"] = int(execution_state.get("attempt_count", 0)) + 1
        execution_state["actor_user_id"] = str(actor_user_id or run.triggered_by_user_id or SYSTEM_ACTOR_ID)
        execution_state["last_started_at"] = self._now().isoformat()
        execution_state.update(execution_patch)

        run.status = IngestionRunStatus.RUNNING
        if run.started_at is None:
            run.started_at = self._now()
        run.run_metadata = self._merge_run_metadata(
            run.run_metadata,
            {"execution": execution_state},
        )
        if persist_running_state:
            await self.db.flush()

        return await self._execute_existing_run(
            run,
            actor_user_id=actor_user_id,
            max_records=selected_max_records,
        )

    async def update_execution_context(
        self,
        run_id: uuid.UUID,
        context: dict[str, Any],
    ) -> IngestionRunDetail:
        run = await self._load_run(run_id)
        run.run_metadata = self._merge_run_metadata(run.run_metadata, {"execution": context})
        await self.db.flush()
        return self._build_detail(run)

    async def list_runs(
        self,
        actor_user: User | None = None,
        *,
        page: int = 1,
        page_size: int = 20,
        status_filter: str | None = None,
        source_key: str | None = None,
        dispatch_status: str | None = None,
    ) -> IngestionRunListResponse:
        if actor_user is not None:
            self._assert_actor_scope(actor_user)
        normalized_status = self._normalize_status_filter(status_filter)
        normalized_source_key = source_key.strip().lower() if isinstance(source_key, str) and source_key.strip() else None
        normalized_dispatch = (
            dispatch_status.strip().lower()
            if isinstance(dispatch_status, str) and dispatch_status.strip()
            else None
        )

        offset = (page - 1) * page_size

        base_query = (
            select(IngestionRun)
            .join(SourceRegistry)
            .options(selectinload(IngestionRun.source_registry))
            .order_by(IngestionRun.created_at.desc())
        )

        if actor_user is not None and actor_user.role == UserRole.UNIVERSITY:
            base_query = base_query.where(IngestionRun.institution_id == actor_user.institution_id)
        if normalized_status is not None:
            base_query = base_query.where(IngestionRun.status == normalized_status)
        if normalized_source_key is not None:
            base_query = base_query.where(
                func.lower(SourceRegistry.source_key) == normalized_source_key
            )

        if normalized_dispatch is not None:
            # dispatch_status lives inside JSON run_metadata — must filter in Python
            result = await self.db.execute(base_query)
            runs = self._result_items(result)
            runs = [run for run in runs if self._read_dispatch_status(run.run_metadata) == normalized_dispatch]
            total = len(runs)
            page_runs = runs[offset : offset + page_size]
        else:
            # Build a separate efficient count query with the same filters
            count_query = (
                select(func.count(IngestionRun.id))
                .select_from(IngestionRun)
                .join(SourceRegistry)
            )
            if actor_user is not None and actor_user.role == UserRole.UNIVERSITY:
                count_query = count_query.where(IngestionRun.institution_id == actor_user.institution_id)
            if normalized_status is not None:
                count_query = count_query.where(IngestionRun.status == normalized_status)
            if normalized_source_key is not None:
                count_query = count_query.where(
                    func.lower(SourceRegistry.source_key) == normalized_source_key
                )
            total_result = await self.db.execute(count_query)
            total = total_result.scalar_one()
            paged_query = base_query.offset(offset).limit(page_size)
            result = await self.db.execute(paged_query)
            page_runs = self._result_items(result)

        items = [self._build_summary(item) for item in page_runs]
        return IngestionRunListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=offset + len(items) < total,
        )

    async def get_run(self, run_id: uuid.UUID, actor_user: User | None = None) -> IngestionRunDetail:
        if actor_user is not None:
            self._assert_actor_scope(actor_user)
        run = await self._load_run(run_id)
        if actor_user is not None:
            self._assert_run_scope(run, actor_user)
        return self._build_detail(run)

    async def retry_run(
        self,
        run_id: uuid.UUID,
        *,
        payload: IngestionRunRetryRequest,
        actor_user: User,
    ) -> IngestionRunDetail:
        self._assert_actor_scope(actor_user)
        run = await self._load_run(run_id)
        self._assert_run_scope(run, actor_user)
        if run.status == IngestionRunStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ingestion run is currently running and cannot be retried",
            )

        requested_mode = payload.execution_mode or self._read_requested_execution_mode(run.run_metadata)
        selected_max_records = payload.max_records or self._read_requested_max_records(run.run_metadata)
        retry_timestamp = self._now().isoformat()
        existing_execution = dict((run.run_metadata or {}).get("execution") or {})
        retry_count = int(existing_execution.get("run_retry_count", 0)) + 1
        run.run_metadata = self._merge_run_metadata(
            run.run_metadata,
            {
                "request": {
                    "max_records": selected_max_records,
                    "execution_mode_requested": requested_mode,
                },
                "execution": {
                    "requested_mode": requested_mode,
                    "last_retry_requested_at": retry_timestamp,
                    "run_retry_count": retry_count,
                    "retry_origin_run_id": str(run.id),
                },
            },
        )
        await self.db.flush()

        execution_context = {
            "requested_mode": requested_mode,
            "retry_triggered": True,
            "last_retry_requested_at": retry_timestamp,
        }

        if requested_mode == "inline":
            execution_context["selected_mode"] = "inline"
            execution_context["dispatch_status"] = "retry_inline"
            return await self.execute_run(
                run.id,
                actor_user_id=actor_user.id,
                max_records=selected_max_records,
                execution_context=execution_context,
            )

        # For worker/auto modes, the route is responsible for Celery dispatch.
        # Return current run detail so the route can enqueue and update context.
        return self._build_detail(run)

    async def assign_review_queue(
        self,
        run_id: uuid.UUID,
        *,
        payload: IngestionRunQueueAssignmentRequest,
        actor_user: User,
    ) -> IngestionRunDetail:
        self._assert_actor_scope(actor_user)
        run = await self._load_run(run_id)
        self._assert_run_scope(run, actor_user)
        assigned_at = self._now().isoformat()
        run.run_metadata = self._merge_run_metadata(
            run.run_metadata,
            {
                "execution": {
                    "review_queue": payload.queue_key,
                    "queue_assigned_by_user_id": str(actor_user.id),
                    "queue_assigned_at": assigned_at,
                    "queue_assignment_note": payload.note,
                }
            },
        )
        await self.db.flush()
        return self._build_detail(run)

    async def bulk_retry_runs(
        self,
        *,
        payload: IngestionRunBulkRetryRequest,
        actor_user: User,
    ) -> IngestionRunBulkRetryResponse:
        items: list[IngestionRunBulkRetryItem] = []
        counts = {"retried": 0, "skipped": 0, "failed": 0}

        for run_id_raw in payload.run_ids:
            try:
                run_id = uuid.UUID(run_id_raw)
            except ValueError:
                counts["failed"] += 1
                items.append(
                    IngestionRunBulkRetryItem(
                        run_id=run_id_raw,
                        status="failed",
                        message="Invalid run id format",
                    )
                )
                continue

            try:
                detail = await self.retry_run(
                    run_id,
                    payload=IngestionRunRetryRequest(
                        max_records=payload.max_records,
                        execution_mode=payload.execution_mode,
                    ),
                    actor_user=actor_user,
                )
                counts["retried"] += 1
                items.append(
                    IngestionRunBulkRetryItem(
                        run_id=run_id_raw,
                        status="retried",
                        message="Run retried successfully",
                        detail=detail,
                    )
                )
            except HTTPException as exc:
                status_label = "skipped" if exc.status_code in {403, 404, 409} else "failed"
                counts[status_label] += 1
                items.append(
                    IngestionRunBulkRetryItem(
                        run_id=run_id_raw,
                        status=status_label,
                        message=str(exc.detail),
                    )
                )
            except Exception:  # pragma: no cover - defensive
                logger.exception("bulk_retry_runs unexpected error run_id=%s", run_id)
                counts["failed"] += 1
                items.append(
                    IngestionRunBulkRetryItem(
                        run_id=run_id_raw,
                        status="failed",
                        message="An unexpected error occurred. Please try again or contact support.",
                    )
                )

        return IngestionRunBulkRetryResponse(
            items=items,
            total=len(items),
            retried=counts["retried"],
            skipped=counts["skipped"],
            failed=counts["failed"],
        )

    async def get_run_snapshot(
        self,
        run_id: uuid.UUID,
        *,
        actor_user: User,
    ) -> IngestionRunSnapshotResponse:
        self._assert_actor_scope(actor_user)
        run = await self._load_run(run_id)
        self._assert_run_scope(run, actor_user)
        snapshot = self._read_snapshot_metadata(run.run_metadata)
        html_content = snapshot.get("html_content")
        has_snapshot = isinstance(html_content, str) and bool(html_content)
        return IngestionRunSnapshotResponse(
            run_id=str(run.id),
            available=has_snapshot,
            html_content=html_content if has_snapshot else None,
            captured_at=snapshot.get("captured_at"),
            content_length=snapshot.get("content_length"),
            truncated=bool(snapshot.get("truncated")),
        )

    async def clear_run_snapshot(
        self,
        run_id: uuid.UUID,
        *,
        actor_user: User,
    ) -> IngestionRunSnapshotResponse:
        self._assert_actor_scope(actor_user)
        run = await self._load_run(run_id)
        self._assert_run_scope(run, actor_user)
        snapshot = self._read_snapshot_metadata(run.run_metadata)
        run.run_metadata = self._merge_run_metadata(
            run.run_metadata,
            {
                "snapshot": {
                    "html_content": None,
                    "captured_at": snapshot.get("captured_at"),
                    "content_length": 0,
                    "truncated": False,
                    "cleared_at": self._now().isoformat(),
                }
            },
        )
        await self.db.flush()
        return IngestionRunSnapshotResponse(
            run_id=str(run.id),
            available=False,
            html_content=None,
            captured_at=snapshot.get("captured_at"),
            content_length=0,
            truncated=False,
        )

    async def _execute_existing_run(
        self,
        run: IngestionRun,
        *,
        actor_user_id: uuid.UUID | None,
        max_records: int,
    ) -> IngestionRunDetail:
        capture: CaptureResult | None = None
        parse_result: ParseCandidatesResult | None = None
        dedup_precheck: dict[str, Any] = {
            "diagnostics": {"candidate_count": 0},
            "advisories": [],
            "skip_matches": {},
        }
        created_records: list[dict[str, Any]] = []
        skipped_records: list[dict[str, Any]] = []
        failed_records: list[dict[str, Any]] = []

        try:
            capture = await self._capture_source(run.fetch_url)
            parse_result = self._parse_candidates(run.source_registry, capture)
            selected_candidates = parse_result.candidates[:max_records]
            dedup_precheck = await self._precheck_existing_candidates(selected_candidates)

            effective_actor_id = actor_user_id or run.triggered_by_user_id or SYSTEM_ACTOR_ID
            actor_context = self._build_actor_context(effective_actor_id)
            curation_service = CurationService(self.db)

            for candidate in selected_candidates:
                prechecked = dedup_precheck["skip_matches"].get(str(candidate.source_url))
                if prechecked is not None:
                    skipped_records.append(
                        self._build_skip_record(
                            candidate,
                            reason=f"duplicate_{prechecked['match_type']}",
                            stage="precheck",
                            existing=prechecked["existing_record"],
                            detail=prechecked.get("detail"),
                        )
                    )
                    continue

                try:
                    detail = await curation_service.import_raw_record(
                        candidate.to_import_request(),
                        actor_context,
                    )
                    created_records.append(
                        {
                            "record_id": detail.record_id,
                            "title": detail.title,
                            "source_url": detail.source_url,
                            "source_document_ref": candidate.source_document_ref,
                        }
                    )
                except HTTPException as exc:
                    if exc.status_code == status.HTTP_409_CONFLICT:
                        skipped_records.append(
                            self._build_skip_record(
                                candidate,
                                reason=self._normalize_duplicate_reason(exc.detail),
                                stage="import_conflict",
                                detail=exc.detail,
                            )
                        )
                        continue
                    failed_records.append(self._build_failure_record(candidate, exc, phase="import"))
                except Exception as exc:  # pragma: no cover - defensive
                    failed_records.append(self._build_failure_record(candidate, exc, phase="import"))

            run.capture_mode = capture.capture_mode
            run.parser_name = "official_page_parser_v3"
            run.records_found = len(parse_result.candidates)
            run.records_created = len(created_records)
            run.records_skipped = len(skipped_records)
            run.completed_at = self._now()
            run.failure_reason = failed_records[0]["error_message"] if failed_records else None
            run.status = self._resolve_run_status(
                records_found=run.records_found,
                records_created=run.records_created,
                records_skipped=run.records_skipped,
                failure_count=len(failed_records),
            )
            run.run_metadata = self._build_run_metadata(
                run=run,
                capture=capture,
                parse_result=parse_result,
                dedup_precheck=dedup_precheck,
                created_records=created_records,
                skipped_records=skipped_records,
                failed_records=failed_records,
                selected_candidate_count=len(selected_candidates),
            )
            await self.db.flush()
            return self._build_detail(run)
        except Exception as exc:
            run.status = IngestionRunStatus.FAILED
            run.completed_at = self._now()
            run.failure_reason = str(exc)
            run.run_metadata = self._merge_run_metadata(
                run.run_metadata,
                {
                    "error_type": exc.__class__.__name__,
                    "failure": {
                        "phase": "capture_or_parse",
                        "error_type": exc.__class__.__name__,
                        "error_message": str(exc),
                        "capture_attempts": getattr(exc, "_capture_attempts", None),
                    },
                    "capture": capture.metadata if capture else None,
                    "parser": parse_result.diagnostics if parse_result else None,
                    "dedup": dedup_precheck.get("diagnostics"),
                    "failed_records": failed_records,
                },
            )
            await self.db.flush()
            raise

    async def _get_or_create_source(
        self, payload: IngestionRunStartRequest, actor_user: User | None = None
    ) -> SourceRegistry:
        result = await self.db.execute(
            select(SourceRegistry).where(SourceRegistry.source_key == payload.source_key)
        )
        source = result.scalar_one_or_none()
        if source is None:
            if not payload.source_display_name or not payload.source_base_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New ingestion sources require source_display_name and source_base_url",
                )
            source = SourceRegistry(
                source_key=payload.source_key,
                display_name=payload.source_display_name,
                base_url=payload.source_base_url,
                source_type=payload.source_type,
                is_active=True,
            )
            self.db.add(source)
            await self.db.flush()
            return source

        if (
            actor_user is not None
            and actor_user.role == UserRole.UNIVERSITY
            and source.institution_id is not None
            and source.institution_id != actor_user.institution_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Source is outside institution scope",
            )

        if payload.source_display_name:
            source.display_name = payload.source_display_name
        if payload.source_base_url:
            source.base_url = payload.source_base_url
        source.source_type = payload.source_type or source.source_type
        source.is_active = True
        return source

    async def _load_run(self, run_id: uuid.UUID) -> IngestionRun:
        result = await self.db.execute(
            select(IngestionRun)
            .where(IngestionRun.id == run_id)
            .options(selectinload(IngestionRun.source_registry))
        )
        run = result.scalar_one_or_none()
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingestion run not found",
            )
        return run

    def _extract_actor_user_id(self, actor_user: User | uuid.UUID | None) -> uuid.UUID:
        if isinstance(actor_user, uuid.UUID):
            return actor_user
        if actor_user is not None:
            return actor_user.id
        return SYSTEM_ACTOR_ID

    def _assert_actor_scope(self, actor_user: User) -> None:
        if actor_user.role == UserRole.UNIVERSITY and not actor_user.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="University user requires institution scope",
            )

    def _assert_run_scope(self, run: IngestionRun, actor_user: User) -> None:
        if actor_user.role == UserRole.UNIVERSITY:
            if run.institution_id is None or run.institution_id != actor_user.institution_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Ingestion run is outside institution scope",
                )

    def _build_actor_context(self, actor_user_id: uuid.UUID) -> User:
        return User(
            id=actor_user_id,
            email="system@scholarai.local",
            password_hash="",
            role=UserRole.ADMIN,
            is_active=True,
            institution_id=None,
            full_name="System Ingestion",
        )

    async def _capture_source(self, url: str) -> CaptureResult:
        attempt_errors: list[dict[str, Any]] = []
        last_exception: Exception | None = None

        for attempt in range(1, MAX_CAPTURE_ATTEMPTS + 1):
            try:
                capture = await self._capture_source_once(url, attempt)
                capture.metadata = {
                    **capture.metadata,
                    "retry_policy": {
                        "max_attempts": MAX_CAPTURE_ATTEMPTS,
                        "base_delay_seconds": CAPTURE_RETRY_BASE_DELAY_SECONDS,
                    },
                    "attempt": attempt,
                    "max_attempts": MAX_CAPTURE_ATTEMPTS,
                    "retries_used": attempt - 1,
                    "attempt_errors": attempt_errors,
                }
                return capture
            except Exception as exc:
                last_exception = exc
                classification = self._classify_capture_error(exc)
                retryable = self._is_retryable_capture_error(exc)
                attempt_errors.append(
                    {
                        "attempt": attempt,
                        "classification": classification,
                        "retryable": retryable,
                        "error_type": exc.__class__.__name__,
                        "error_message": str(exc),
                    }
                )
                if not retryable:
                    break
                if attempt < MAX_CAPTURE_ATTEMPTS:
                    await asyncio.sleep(self._capture_backoff_delay(attempt))

        assert last_exception is not None
        setattr(last_exception, "_capture_attempts", attempt_errors)
        raise last_exception

    def _capture_backoff_delay(self, attempt: int) -> float:
        exponential = CAPTURE_RETRY_BASE_DELAY_SECONDS * (2 ** max(attempt - 1, 0))
        jitter = random.uniform(0.0, 0.25)
        return round(exponential + jitter, 3)

    def _classify_capture_error(self, exc: Exception) -> str:
        if isinstance(exc, HTTPException):
            return "http_exception"
        if isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code
            if 500 <= status_code <= 599:
                return "server_http_status"
            if status_code in {408, 425, 429}:
                return "rate_limited_or_timeout"
            return "client_http_status"
        if isinstance(
            exc,
            (
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
                TimeoutError,
                asyncio.TimeoutError,
            ),
        ):
            return "timeout"
        if isinstance(exc, (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError, OSError)):
            return "transient_network"
        if isinstance(exc, (ValueError, TypeError)):
            return "invalid_payload"
        return "unknown"

    def _is_retryable_capture_error(self, exc: Exception) -> bool:
        classification = self._classify_capture_error(exc)
        if classification in {"timeout", "transient_network", "rate_limited_or_timeout", "server_http_status"}:
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            return 500 <= exc.response.status_code <= 599
        return False

    async def _capture_source_once(self, url: str, attempt: int) -> CaptureResult:
        transport_errors: list[dict[str, Any]] = []
        user_agent = "ScholarAI-Internal-Ingestion/0.1"

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=45_000)
                html = await page.content()
                title = await page.title()
                final_url = page.url
                await browser.close()
                return CaptureResult(
                    html=html,
                    final_url=final_url,
                    title=title,
                    capture_mode="playwright",
                    metadata={
                        "requested_url": url,
                        "final_url": final_url,
                        "page_title": title,
                        "attempt": attempt,
                        "transport_errors": transport_errors,
                    },
                )
        except Exception as exc:
            transport_errors.append(
                {
                    "transport": "playwright",
                    "error_type": exc.__class__.__name__,
                    "error_message": str(exc),
                }
            )

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url, headers={"User-Agent": user_agent})
            tls_mode = "verified"
        except httpx.HTTPError as exc:
            transport_errors.append(
                {
                    "transport": "httpx_verified",
                    "error_type": exc.__class__.__name__,
                    "error_message": str(exc),
                }
            )
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0, verify=False) as client:
                response = await client.get(url, headers={"User-Agent": user_agent})
            tls_mode = "insecure_retry"

        response.raise_for_status()
        html = response.text
        title = self._extract_title(html)
        return CaptureResult(
            html=html,
            final_url=str(response.url),
            title=title,
            capture_mode="httpx_fallback",
            metadata={
                "requested_url": url,
                "final_url": str(response.url),
                "page_title": title,
                "status_code": response.status_code,
                "tls_mode": tls_mode,
                "attempt": attempt,
                "transport_errors": transport_errors,
            },
        )

    def _parse_candidates(
        self,
        source: SourceRegistry,
        capture: CaptureResult,
    ) -> ParseCandidatesResult:
        soup = BeautifulSoup(capture.html, "html.parser")
        page_summary = self._extract_meta_description(soup)
        page_title = self._clean_text(capture.title or self._extract_title(capture.html) or source.display_name)
        page_text = self._clean_text(soup.get_text(" ", strip=True))[:MAX_CONTEXT_TEXT_LENGTH]
        base_host = urlparse(capture.final_url).netloc

        candidates: list[ParsedScholarshipCandidate] = []
        seen_urls: set[str] = set()
        diagnostics = {
            "anchor_candidates": 0,
            "table_candidates": 0,
            "jsonld_candidates": 0,
            "fallback_used": False,
            "same_host": base_host,
        }

        for anchor in soup.select("a[href]"):
            candidate = self._candidate_from_anchor(
                source=source,
                capture=capture,
                anchor=anchor,
                page_summary=page_summary,
                page_title=page_title,
                base_host=base_host,
            )
            if candidate is None:
                continue
            candidate_url = str(candidate.source_url)
            if candidate_url in seen_urls:
                continue
            seen_urls.add(candidate_url)
            candidates.append(candidate)
            diagnostics["anchor_candidates"] += 1

        for row in soup.select("table tr"):
            candidate = self._candidate_from_table_row(
                source=source,
                capture=capture,
                row=row,
                page_summary=page_summary,
                page_title=page_title,
                base_host=base_host,
            )
            if candidate is None:
                continue
            candidate_url = str(candidate.source_url)
            if candidate_url in seen_urls:
                continue
            seen_urls.add(candidate_url)
            candidates.append(candidate)
            diagnostics["table_candidates"] += 1

        for candidate in self._candidates_from_jsonld(
            source=source,
            capture=capture,
            soup=soup,
            page_summary=page_summary,
            page_title=page_title,
            base_host=base_host,
        ):
            candidate_url = str(candidate.source_url)
            if candidate_url in seen_urls:
                continue
            seen_urls.add(candidate_url)
            candidates.append(candidate)
            diagnostics["jsonld_candidates"] += 1

        if not candidates and self._candidate_text_in_scope(source, f"{page_title} {page_summary or ''} {page_text}"):
            fallback_candidate = self._build_candidate(
                source=source,
                capture=capture,
                resolved_url=capture.final_url,
                title=page_title,
                combined_text=f"{page_title} {page_summary or ''} {page_text}",
                context_text=page_summary or page_text,
                parse_origin="page_fallback",
            )
            if fallback_candidate is not None:
                diagnostics["fallback_used"] = True
                candidates.append(fallback_candidate)

        diagnostics["candidate_count"] = len(candidates)
        return ParseCandidatesResult(candidates=candidates, diagnostics=diagnostics)

    def _candidates_from_jsonld(
        self,
        *,
        source: SourceRegistry,
        capture: CaptureResult,
        soup: BeautifulSoup,
        page_summary: str | None,
        page_title: str,
        base_host: str,
    ) -> list[ParsedScholarshipCandidate]:
        candidates: list[ParsedScholarshipCandidate] = []
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            raw = script.string or script.get_text(" ", strip=True)
            if not raw:
                continue
            parsed_payload = self._parse_jsonld_payload(raw)
            if parsed_payload is None:
                continue
            for item in self._flatten_jsonld_items(parsed_payload):
                candidate = self._candidate_from_jsonld_item(
                    source=source,
                    capture=capture,
                    item=item,
                    page_summary=page_summary,
                    page_title=page_title,
                    base_host=base_host,
                )
                if candidate is not None:
                    candidates.append(candidate)
        return candidates

    def _parse_jsonld_payload(self, raw: str) -> Any | None:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def _flatten_jsonld_items(self, payload: Any) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        queue: deque[Any] = deque([payload])
        while queue:
            current = queue.popleft()
            if isinstance(current, list):
                queue.extend(current)
                continue
            if not isinstance(current, dict):
                continue
            graph_items = current.get("@graph")
            if isinstance(graph_items, list):
                queue.extend(graph_items)
            list_items = current.get("itemListElement")
            if isinstance(list_items, list):
                queue.extend(list_items)
            nested_item = current.get("item")
            if isinstance(nested_item, (dict, list)):
                queue.append(nested_item)
            items.append(current)
        return items

    def _candidate_from_jsonld_item(
        self,
        *,
        source: SourceRegistry,
        capture: CaptureResult,
        item: dict[str, Any],
        page_summary: str | None,
        page_title: str,
        base_host: str,
    ) -> ParsedScholarshipCandidate | None:
        type_value = item.get("@type")
        type_values: list[str]
        if isinstance(type_value, str):
            type_values = [type_value.lower()]
        elif isinstance(type_value, list):
            type_values = [str(value).lower() for value in type_value]
        else:
            type_values = []

        if not any(
            any(token in value for token in ("scholarship", "grant", "fellowship", "educationaloccupationalprogram"))
            for value in type_values
        ):
            return None

        resolved_url = self._resolve_jsonld_url(item=item, capture=capture)
        if resolved_url is None:
            return None
        parsed_url = urlparse(resolved_url)
        if parsed_url.scheme not in {"http", "https"}:
            return None
        if parsed_url.netloc and parsed_url.netloc != base_host:
            return None

        raw_title = item.get("name") or item.get("headline") or page_title
        title = self._clean_text(str(raw_title))
        if len(title) < 3:
            return None

        description = item.get("description")
        description_text = self._clean_text(str(description)) if isinstance(description, str) else ""
        combined_text = self._clean_text(f"{title} {description_text} {page_summary or ''}")
        if not self._candidate_text_in_scope(source, combined_text):
            return None

        return self._build_candidate(
            source=source,
            capture=capture,
            resolved_url=resolved_url,
            title=title,
            combined_text=combined_text,
            context_text=description_text or page_summary or page_title,
            parse_origin="jsonld",
        )

    def _resolve_jsonld_url(
        self,
        *,
        item: dict[str, Any],
        capture: CaptureResult,
    ) -> str | None:
        url_candidate = item.get("url")
        if not isinstance(url_candidate, str) or not url_candidate.strip():
            main_entity = item.get("mainEntityOfPage")
            if isinstance(main_entity, str):
                url_candidate = main_entity
            elif isinstance(main_entity, dict):
                if isinstance(main_entity.get("url"), str):
                    url_candidate = main_entity.get("url")
                elif isinstance(main_entity.get("@id"), str):
                    url_candidate = main_entity.get("@id")
            elif isinstance(item.get("@id"), str):
                url_candidate = item.get("@id")

        if not isinstance(url_candidate, str) or not url_candidate.strip():
            return None
        return urljoin(capture.final_url, url_candidate.strip())

    async def _precheck_existing_candidates(
        self,
        candidates: list[ParsedScholarshipCandidate],
    ) -> dict[str, Any]:
        skip_matches: dict[str, dict[str, Any]] = {}
        advisories: list[dict[str, Any]] = []
        diagnostics = {
            "candidate_count": len(candidates),
            "source_url_matches": 0,
            "content_hash_matches": 0,
            "source_document_ref_matches": 0,
            "duplicate_candidates_in_run": 0,
        }
        seen_content_hashes: dict[str, str] = {}

        for candidate in candidates:
            candidate_url = str(candidate.source_url)
            content_hash = self._compute_content_hash(candidate)

            if content_hash in seen_content_hashes:
                diagnostics["duplicate_candidates_in_run"] += 1
                skip_matches[candidate_url] = {
                    "match_type": "content_hash",
                    "detail": "Duplicate content detected within the same ingestion run",
                    "existing_record": {
                        "source_url": seen_content_hashes[content_hash],
                        "content_hash": content_hash,
                    },
                }
                continue

            seen_content_hashes[content_hash] = candidate_url

            existing_url = await self._find_existing_scholarship(Scholarship.source_url == candidate_url)
            if existing_url is not None:
                diagnostics["source_url_matches"] += 1
                skip_matches[candidate_url] = {
                    "match_type": "source_url",
                    "detail": "Existing scholarship already uses this source URL",
                    "existing_record": self._snapshot_existing_record(existing_url),
                }
                continue

            existing_hash = await self._find_existing_scholarship(Scholarship.content_hash == content_hash)
            if existing_hash is not None:
                diagnostics["content_hash_matches"] += 1
                skip_matches[candidate_url] = {
                    "match_type": "content_hash",
                    "detail": "Existing scholarship already has identical content hash",
                    "existing_record": self._snapshot_existing_record(existing_hash),
                }
                continue

            if candidate.source_document_ref:
                existing_ref = await self._find_existing_scholarship(
                    Scholarship.source_document_ref == candidate.source_document_ref
                )
                if existing_ref is not None:
                    diagnostics["source_document_ref_matches"] += 1
                    advisories.append(
                        {
                            "title": candidate.title,
                            "source_url": candidate_url,
                            "source_document_ref": candidate.source_document_ref,
                            "existing_record": self._snapshot_existing_record(existing_ref),
                        }
                    )

        return {
            "skip_matches": skip_matches,
            "advisories": advisories,
            "diagnostics": diagnostics,
        }

    async def _find_existing_scholarship(self, where_clause: Any) -> Scholarship | None:
        result = await self.db.execute(select(Scholarship).where(where_clause))
        record = result.scalar_one_or_none()
        return record if isinstance(record, Scholarship) else None

    def _candidate_from_anchor(
        self,
        *,
        source: SourceRegistry,
        capture: CaptureResult,
        anchor: Tag,
        page_summary: str | None,
        page_title: str,
        base_host: str,
    ) -> ParsedScholarshipCandidate | None:
        href = (anchor.get("href") or "").strip()
        if not href:
            return None
        resolved_url = urljoin(capture.final_url, href)
        parsed_url = urlparse(resolved_url)
        if parsed_url.scheme not in {"http", "https"}:
            return None
        if parsed_url.netloc and parsed_url.netloc != base_host:
            return None

        context_node = anchor.find_parent(CONTEXT_CONTAINERS)
        anchor_text = self._clean_text(anchor.get_text(" ", strip=True))
        context_text = self._extract_context_text(context_node or anchor)
        title = self._derive_title(anchor_text, context_node, page_title)
        combined_text = self._clean_text(f"{title} {context_text} {page_summary or ''}")
        if not self._candidate_text_in_scope(source, combined_text):
            return None
        return self._build_candidate(
            source=source,
            capture=capture,
            resolved_url=resolved_url,
            title=title,
            combined_text=combined_text,
            context_text=context_text or page_summary or page_title,
            parse_origin="anchor",
        )

    def _candidate_from_table_row(
        self,
        *,
        source: SourceRegistry,
        capture: CaptureResult,
        row: Tag,
        page_summary: str | None,
        page_title: str,
        base_host: str,
    ) -> ParsedScholarshipCandidate | None:
        anchor = row.find("a", href=True)
        if anchor is None:
            return None
        href = (anchor.get("href") or "").strip()
        if not href:
            return None
        resolved_url = urljoin(capture.final_url, href)
        parsed_url = urlparse(resolved_url)
        if parsed_url.scheme not in {"http", "https"}:
            return None
        if parsed_url.netloc and parsed_url.netloc != base_host:
            return None

        cells = row.find_all(["th", "td"])
        title = ""
        for cell in cells:
            cell_text = self._clean_text(cell.get_text(" ", strip=True))
            if cell_text and cell_text.lower() not in GENERIC_LINK_TEXT:
                title = cell_text
                break
        if not title:
            title = self._derive_title(self._clean_text(anchor.get_text(" ", strip=True)), row, page_title)
        context_text = self._extract_context_text(row)
        combined_text = self._clean_text(f"{title} {context_text} {page_summary or ''}")
        if not self._candidate_text_in_scope(source, combined_text):
            return None
        return self._build_candidate(
            source=source,
            capture=capture,
            resolved_url=resolved_url,
            title=title,
            combined_text=combined_text,
            context_text=context_text or page_summary or page_title,
            parse_origin="table_row",
        )

    def _build_candidate(
        self,
        *,
        source: SourceRegistry,
        capture: CaptureResult,
        resolved_url: str,
        title: str,
        combined_text: str,
        context_text: str,
        parse_origin: str,
    ) -> ParsedScholarshipCandidate | None:
        cleaned_title = self._clean_text(title)
        if len(cleaned_title) < 3:
            return None

        field_tags = self._infer_field_tags(combined_text)
        if not field_tags and not self._is_fulbright_source(f"{source.source_key} {source.display_name} {resolved_url}"):
            return None

        timestamp = self._now()
        return ParsedScholarshipCandidate(
            source_key=source.source_key,
            source_display_name=source.display_name,
            source_base_url=source.base_url,
            source_type=source.source_type,
            title=cleaned_title,
            provider_name=source.display_name,
            country_code=self._infer_country_code(source, resolved_url),
            source_url=resolved_url,
            summary=self._build_candidate_summary(cleaned_title, context_text),
            funding_summary=self._extract_funding_summary(combined_text),
            field_tags=field_tags,
            degree_levels=self._infer_degree_levels(combined_text),
            citizenship_rules=[],
            source_document_ref=self._document_ref_from_url_or_title(resolved_url, cleaned_title),
            imported_at=timestamp,
            source_last_seen_at=timestamp,
            review_notes="Auto-imported from source registry page for curator review.",
            provenance_payload={
                "ingested_via": "source_registry_run",
                "capture_mode": capture.capture_mode,
                "capture_title": capture.title,
                "parse_origin": parse_origin,
                "matched_text": combined_text[:MAX_CONTEXT_TEXT_LENGTH],
            },
        )

    def _extract_context_text(self, node: Tag | None) -> str:
        if node is None:
            return ""
        text = self._clean_text(node.get_text(" ", strip=True))
        return text[:MAX_CONTEXT_TEXT_LENGTH]

    def _derive_title(self, anchor_text: str, context_node: Tag | None, page_title: str) -> str:
        cleaned_anchor = self._clean_text(anchor_text)
        if cleaned_anchor and cleaned_anchor.lower() not in GENERIC_LINK_TEXT:
            return cleaned_anchor

        if context_node is not None:
            if context_node.name == "tr":
                for cell in context_node.find_all(["th", "td"]):
                    cell_text = self._clean_text(cell.get_text(" ", strip=True))
                    if cell_text and cell_text.lower() not in GENERIC_LINK_TEXT:
                        return cell_text
            for tag_name in TITLE_CANDIDATE_TAGS:
                node = context_node.find(tag_name)
                if node is None:
                    continue
                node_text = self._clean_text(node.get_text(" ", strip=True))
                if node_text and node_text.lower() not in GENERIC_LINK_TEXT:
                    return node_text

            context_text = self._extract_context_text(context_node)
            if context_text:
                return context_text[:255]

        return page_title

    def _candidate_text_in_scope(self, source: SourceRegistry, text: str) -> bool:
        normalized = f" {self._clean_text(text).lower()} "
        if not any(keyword in normalized for keyword in SCHOLARSHIP_KEYWORDS):
            return False
        if self._is_fulbright_source(f"{source.source_key} {source.display_name} {normalized}"):
            return True
        return bool(self._infer_field_tags(normalized))

    def _is_fulbright_source(self, text: str) -> bool:
        lowered = text.lower()
        return "fulbright" in lowered or "foreign.fulbright" in lowered

    def _compute_content_hash(self, candidate: ParsedScholarshipCandidate) -> str:
        content_string = f"{candidate.title}|{candidate.summary or ''}|{candidate.provider_name or ''}"
        return hashlib.sha256(content_string.encode()).hexdigest()

    def _snapshot_existing_record(self, record: Scholarship) -> dict[str, Any]:
        return {
            "record_id": str(record.id),
            "title": record.title,
            "source_url": record.source_url,
            "source_document_ref": record.source_document_ref,
            "content_hash": record.content_hash,
        }

    def _build_snapshot_metadata(self, capture: CaptureResult) -> dict[str, Any]:
        html = capture.html or ""
        truncated = len(html) > MAX_CAPTURED_SNAPSHOT_CHARS
        stored_html = html[:MAX_CAPTURED_SNAPSHOT_CHARS]
        return {
            "html_content": stored_html,
            "captured_at": self._now().isoformat(),
            "content_length": len(stored_html),
            "truncated": truncated,
            "capture_mode": capture.capture_mode,
            "final_url": capture.final_url,
        }

    def _read_snapshot_metadata(self, run_metadata: dict[str, Any] | None) -> dict[str, Any]:
        metadata = run_metadata if isinstance(run_metadata, dict) else {}
        snapshot = metadata.get("snapshot")
        return snapshot if isinstance(snapshot, dict) else {}

    def _build_skip_record(
        self,
        candidate: ParsedScholarshipCandidate,
        *,
        reason: str,
        stage: str,
        existing: dict[str, Any] | None = None,
        detail: Any = None,
    ) -> dict[str, Any]:
        record = {
            "title": candidate.title,
            "source_url": str(candidate.source_url),
            "source_document_ref": candidate.source_document_ref,
            "reason": reason,
            "stage": stage,
        }
        if existing is not None:
            record["existing_record"] = existing
        if detail is not None:
            record["detail"] = detail
        return record

    def _build_failure_record(
        self,
        candidate: ParsedScholarshipCandidate,
        exc: Exception,
        *,
        phase: str,
    ) -> dict[str, Any]:
        return {
            "title": candidate.title,
            "source_url": str(candidate.source_url),
            "source_document_ref": candidate.source_document_ref,
            "phase": phase,
            "error_type": exc.__class__.__name__,
            "error_message": str(exc),
        }

    def _normalize_duplicate_reason(self, detail: Any) -> str:
        message = str(detail).lower()
        if "identical content" in message or "content" in message:
            return "duplicate_content_hash"
        if "source url" in message:
            return "duplicate_source_url"
        return "duplicate_record"

    def _base_run_metadata(
        self,
        *,
        source: SourceRegistry,
        payload: IngestionRunStartRequest,
        actor_user_id: uuid.UUID | None,
    ) -> RunMetadata:
        return RunMetadata(
            {
                "source": {
                    "source_key": source.source_key,
                    "source_display_name": source.display_name,
                    "source_base_url": source.base_url,
                    "source_type": source.source_type,
                    "scope_policy": "canada_first_fulbright_us_only",
                },
                "request": {
                    "max_records": payload.max_records,
                    "execution_mode_requested": payload.execution_mode,
                },
                "execution": {
                    "selected_mode": None,
                    "dispatch_status": "created",
                    "actor_user_id": str(actor_user_id) if actor_user_id else None,
                    "attempt_count": 0,
                    "retry_count": 0,
                },
                "capture": {},
                "parser": {},
                "dedup": {},
                "created_records": [],
                "skipped_records": [],
                "failed_records": [],
            }
        )

    def _build_run_metadata(
        self,
        *,
        run: IngestionRun,
        capture: CaptureResult,
        parse_result: ParseCandidatesResult,
        dedup_precheck: dict[str, Any],
        created_records: list[dict[str, Any]],
        skipped_records: list[dict[str, Any]],
        failed_records: list[dict[str, Any]],
        selected_candidate_count: int,
    ) -> RunMetadata:
        execution_state = dict((run.run_metadata or {}).get("execution") or {})
        execution_state["retry_count"] = int(capture.metadata.get("retries_used", 0))
        execution_state["completed_at"] = self._now().isoformat()

        return self._merge_run_metadata(
            run.run_metadata,
            {
                "execution": execution_state,
                "summary": {
                    "records_found": run.records_found,
                    "records_created": run.records_created,
                    "records_skipped": run.records_skipped,
                    "failed_records": len(failed_records),
                    "selected_candidate_count": selected_candidate_count,
                },
                "capture": capture.metadata,
                "snapshot": self._build_snapshot_metadata(capture),
                "parser": parse_result.diagnostics,
                "dedup": {
                    **dedup_precheck["diagnostics"],
                    "advisories": dedup_precheck["advisories"],
                },
                "created_records": created_records,
                "skipped_records": skipped_records,
                "failed_records": failed_records,
            },
        )

    def _merge_run_metadata(
        self,
        existing: dict[str, Any] | None,
        patch: dict[str, Any],
    ) -> RunMetadata:
        base = self._deep_copy_dict(existing or {})
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                base[key] = self._merge_run_metadata(base[key], value)
            else:
                base[key] = value
        return RunMetadata(base)

    def _deep_copy_dict(self, value: dict[str, Any]) -> dict[str, Any]:
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if isinstance(item, dict):
                copied[key] = self._deep_copy_dict(item)
            elif isinstance(item, list):
                copied[key] = [self._deep_copy_dict(v) if isinstance(v, dict) else v for v in item]
            else:
                copied[key] = item
        return copied

    def _read_requested_max_records(self, run_metadata: dict[str, Any] | None) -> int:
        request = dict((run_metadata or {}).get("request") or {})
        max_records = request.get("max_records", DEFAULT_MAX_RECORDS)
        try:
            return int(max_records)
        except (TypeError, ValueError):
            return DEFAULT_MAX_RECORDS

    def _read_requested_execution_mode(self, run_metadata: dict[str, Any] | None) -> str:
        request = dict((run_metadata or {}).get("request") or {})
        execution = dict((run_metadata or {}).get("execution") or {})
        requested_mode = (
            request.get("execution_mode_requested")
            or execution.get("requested_mode")
            or execution.get("selected_mode")
            or "inline"
        )
        if requested_mode in {"auto", "worker", "inline"}:
            return requested_mode
        return "inline"

    def _read_dispatch_status(self, run_metadata: dict[str, Any] | None) -> str:
        execution = dict((run_metadata or {}).get("execution") or {})
        dispatch = execution.get("dispatch_status")
        return dispatch.strip().lower() if isinstance(dispatch, str) and dispatch.strip() else ""

    def _normalize_status_filter(self, status_filter: str | None) -> IngestionRunStatus | None:
        if not status_filter:
            return None
        normalized = status_filter.strip().lower()
        if not normalized:
            return None
        try:
            return IngestionRunStatus(normalized)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ingestion run status filter",
            ) from exc

    def _result_items(self, result: Any) -> list[Any]:
        scalars = getattr(result, "scalars", None)
        if callable(scalars):
            scalar_result = scalars()
            all_method = getattr(scalar_result, "all", None)
            if callable(all_method):
                return list(all_method())
        item = getattr(result, "item", None)
        return [item] if item is not None else []

    def _build_candidate_summary(self, title: str, context_text: str | None) -> str:
        summary = self._clean_text(context_text or "")
        if summary:
            trimmed = summary[:MAX_SUMMARY_LENGTH]
            if trimmed.lower().startswith(title.lower()):
                return trimmed
            return f"{title}. {trimmed}"[: MAX_SUMMARY_LENGTH + len(title) + 2]
        return f"{title}. Imported from the approved source registry for curator review."

    def _extract_funding_summary(self, text: str) -> str | None:
        lowered = text.lower()
        for keyword in ("stipend", "tuition", "funding", "award", "grant", "bursary"):
            if keyword in lowered:
                return (
                    f"Potential {keyword}-related support mentioned on the source page; "
                    "curator verification required."
                )
        return None

    def _infer_field_tags(self, text: str) -> list[str]:
        lowered = f" {text.lower()} "
        matched = [
            canonical
            for canonical, keywords in FIELD_KEYWORD_MAP.items()
            if any(keyword in lowered for keyword in keywords)
        ]
        return matched

    def _infer_degree_levels(self, text: str) -> list[str]:
        lowered = f" {text.lower()} "
        levels = [level for level, keywords in DEGREE_KEYWORDS if any(keyword in lowered for keyword in keywords)]
        return levels or ["MS"]

    def _infer_country_code(self, source: SourceRegistry, url: str) -> str:
        lowered = f"{source.source_key} {source.display_name} {url}".lower()
        if "fulbright" in lowered or "foreign.fulbright" in lowered:
            return "US"
        return "CA"

    def _document_ref_from_url_or_title(self, resolved_url: str, title: str) -> str:
        path_segments = [segment for segment in urlparse(resolved_url).path.split("/") if segment]
        if path_segments:
            return self._slugify(path_segments[-1])
        return self._slugify(title)

    def _extract_title(self, html: str) -> str | None:
        match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return self._clean_text(match.group(1))

    def _extract_meta_description(self, soup: BeautifulSoup) -> str | None:
        meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"}
        )
        if meta is None:
            return None
        content = meta.get("content")
        return self._clean_text(content) if content else None

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug[:255] or "item"

    def _resolve_run_status(
        self,
        *,
        records_found: int,
        records_created: int,
        records_skipped: int,
        failure_count: int,
    ) -> IngestionRunStatus:
        if records_created > 0 and records_skipped == 0 and failure_count == 0 and records_found == records_created:
            return IngestionRunStatus.COMPLETED
        if records_created > 0 or records_skipped > 0 or failure_count > 0 or records_found > 0:
            return IngestionRunStatus.PARTIAL
        return IngestionRunStatus.FAILED

    def _build_summary(self, run: IngestionRun) -> IngestionRunSummary:
        metadata = run.run_metadata or {}
        execution = metadata.get("execution") or {}
        request = metadata.get("request") or {}
        failure = metadata.get("failure") or {}
        snapshot = self._read_snapshot_metadata(metadata)

        def _as_int(value: Any) -> int:
            try:
                return int(value) if value is not None else 0
            except (TypeError, ValueError):
                return 0

        return IngestionRunSummary(
            run_id=str(run.id),
            source_key=run.source_registry.source_key,
            source_display_name=run.source_registry.display_name,
            fetch_url=run.fetch_url,
            status=run.status.value,
            capture_mode=run.capture_mode,
            parser_name=run.parser_name,
            records_found=_as_int(run.records_found),
            records_created=_as_int(run.records_created),
            records_skipped=_as_int(run.records_skipped),
            failure_reason=run.failure_reason,
            started_at=run.started_at,
            completed_at=run.completed_at,
            created_at=run.created_at,
            execution_mode_requested=request.get("execution_mode_requested"),
            execution_mode_selected=execution.get("selected_mode"),
            dispatch_status=execution.get("dispatch_status"),
            celery_task_id=execution.get("celery_task_id"),
            attempt_count=_as_int(execution.get("attempt_count"))
            if execution.get("attempt_count") is not None
            else None,
            run_retry_count=_as_int(execution.get("run_retry_count"))
            if execution.get("run_retry_count") is not None
            else None,
            last_started_at=execution.get("last_started_at"),
            last_retry_requested_at=execution.get("last_retry_requested_at"),
            failure_phase=failure.get("phase"),
            review_queue=execution.get("review_queue"),
            queue_assigned_by_user_id=execution.get("queue_assigned_by_user_id"),
            queue_assigned_at=execution.get("queue_assigned_at"),
            queue_assignment_note=execution.get("queue_assignment_note"),
            snapshot_available=bool(snapshot.get("html_content")),
            snapshot_captured_at=snapshot.get("captured_at"),
            snapshot_content_length=_as_int(snapshot.get("content_length"))
            if snapshot.get("content_length") is not None
            else None,
        )

    def _build_detail(self, run: IngestionRun) -> IngestionRunDetail:
        return IngestionRunDetail(
            **self._build_summary(run).model_dump(),
            run_metadata=run.run_metadata,
        )

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)
