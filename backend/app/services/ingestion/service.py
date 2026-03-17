from __future__ import annotations

import asyncio
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import IngestionRun, IngestionRunStatus, SourceRegistry
from app.schemas.curation import (
    CurationRawImportRequest,
    IngestionRunDetail,
    IngestionRunListResponse,
    IngestionRunStartRequest,
    IngestionRunSummary,
)
from app.services.curation import CurationService

SCHOLARSHIP_KEYWORDS = (
    "scholarship",
    "award",
    "funding",
    "grant",
    "fellowship",
    "bursary",
)
FIELD_KEYWORD_MAP = {
    "data science": ["data science", "data-science", "data scientist"],
    "artificial intelligence": ["artificial intelligence", "ai", "machine learning"],
    "analytics": ["analytics", "business analytics", "data analytics"],
}
DEGREE_KEYWORDS = ("master", "masters", "m.sc", "msc", "ms ")

from functools import wraps

def retry_async(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt)) # Exponential backoff
            raise last_exception
        return wrapper
    return decorator


@dataclass
class CaptureResult:
    html: str
    final_url: str
    title: str | None
    capture_mode: str
    metadata: dict[str, Any]


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
        actor_user_id: uuid.UUID,
    ) -> IngestionRunDetail:
        source = await self._get_or_create_source(payload)
        run = IngestionRun(
            source_registry=source,
            triggered_by_user_id=actor_user_id,
            status=IngestionRunStatus.RUNNING,
            fetch_url=source.base_url,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        await self.db.flush()

        try:
            capture = await self._capture_source(source.base_url)
            candidates = self._parse_candidates(source, capture)
            curation_service = CurationService(self.db)
            created: list[dict[str, str]] = []
            skipped: list[dict[str, str]] = []

            for candidate in candidates[: payload.max_records]:
                try:
                    detail = await curation_service.import_raw_record(
                        candidate.to_import_request(),
                        actor_user_id,
                    )
                    created.append(
                        {
                            "record_id": detail.record_id,
                            "title": detail.title,
                            "source_url": detail.source_url,
                        }
                    )
                except HTTPException as exc:
                    if exc.status_code != status.HTTP_409_CONFLICT:
                        raise
                    skipped.append(
                        {
                            "title": candidate.title,
                            "source_url": str(candidate.source_url),
                            "reason": "duplicate_source_url",
                        }
                    )

            run.capture_mode = capture.capture_mode
            run.parser_name = "playwright_pandas_pydantic_v1"
            run.records_found = len(candidates)
            run.records_created = len(created)
            run.records_skipped = len(skipped)
            run.completed_at = datetime.now(timezone.utc)
            run.run_metadata = {
                "created_records": created,
                "skipped_records": skipped,
                "capture": capture.metadata,
            }
            run.failure_reason = None
            run.status = self._resolve_run_status(run.records_found, run.records_created, run.records_skipped)
            await self.db.flush()
            return self._build_detail(run)
        except Exception as exc:
            run.status = IngestionRunStatus.FAILED
            run.completed_at = datetime.now(timezone.utc)
            run.failure_reason = str(exc)
            run.run_metadata = {"error_type": exc.__class__.__name__}
            await self.db.flush()
            raise

    async def list_runs(self, limit: int = 20) -> IngestionRunListResponse:
        result = await self.db.execute(
            select(IngestionRun)
            .options(selectinload(IngestionRun.source_registry))
            .order_by(IngestionRun.created_at.desc())
            .limit(limit)
        )
        items = [self._build_summary(item) for item in result.scalars().all()]
        return IngestionRunListResponse(items=items, total=len(items))

    async def get_run(self, run_id: uuid.UUID) -> IngestionRunDetail:
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
        return self._build_detail(run)

    async def _get_or_create_source(self, payload: IngestionRunStartRequest) -> SourceRegistry:
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

        if payload.source_display_name:
            source.display_name = payload.source_display_name
        if payload.source_base_url:
            source.base_url = payload.source_base_url
        source.source_type = payload.source_type or source.source_type
        source.is_active = True
        return source

    @retry_async(max_retries=2, delay=2.0)
    async def _capture_source(self, url: str) -> CaptureResult:
        capture_errors: list[str] = []
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
                    },
                )
        except Exception as exc:
            capture_errors.append(str(exc))

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
            ) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "ScholarAI-Internal-Ingestion/0.1"},
                )
        except httpx.HTTPError as exc:
            capture_errors.append(str(exc))
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
                verify=False,
            ) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "ScholarAI-Internal-Ingestion/0.1"},
                )

            tls_mode = "insecure_retry"
        else:
            tls_mode = "verified"

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
                "playwright_errors": capture_errors,
            },
        )

    def _parse_candidates(
        self,
        source: SourceRegistry,
        capture: CaptureResult,
    ) -> list[ParsedScholarshipCandidate]:
        soup = BeautifulSoup(capture.html, "lxml")
        page_text = soup.get_text(" ", strip=True)
        page_summary = self._extract_meta_description(soup)
        table_records = self._extract_table_records(capture.html)
        table_text = " ".join(
            " ".join(str(value) for value in row.values())
            for table in table_records
            for row in table[:8]
        )

        candidates: list[ParsedScholarshipCandidate] = []
        seen_urls: set[str] = set()
        base_host = urlparse(capture.final_url).netloc

        for anchor in soup.select("a[href]"):
            text = self._clean_text(anchor.get_text(" ", strip=True))
            href = anchor.get("href", "").strip()
            if not text or not href:
                continue

            resolved_url = urljoin(capture.final_url, href)
            parsed = urlparse(resolved_url)
            if parsed.scheme not in {"http", "https"}:
                continue
            if parsed.netloc and parsed.netloc != base_host:
                continue
            if resolved_url in seen_urls:
                continue
            if not self._looks_like_candidate(text):
                continue

            combined_text = f"{text} {page_summary} {table_text}"
            field_tags = self._infer_field_tags(combined_text)
            if not field_tags and "fulbright" not in source.source_key.lower():
                continue

            seen_urls.add(resolved_url)
            candidates.append(
                ParsedScholarshipCandidate(
                    source_key=source.source_key,
                    source_display_name=source.display_name,
                    source_base_url=source.base_url,
                    source_type=source.source_type,
                    title=text,
                    provider_name=source.display_name,
                    country_code=self._infer_country_code(source, resolved_url),
                    source_url=resolved_url,
                    summary=self._build_candidate_summary(text, page_summary),
                    funding_summary=self._extract_funding_summary(combined_text),
                    field_tags=field_tags,
                    degree_levels=self._infer_degree_levels(combined_text),
                    citizenship_rules=[],
                    source_document_ref=self._slugify(text),
                    imported_at=datetime.now(timezone.utc),
                    source_last_seen_at=datetime.now(timezone.utc),
                    review_notes="Auto-imported from source registry page for curator review.",
                    provenance_payload={
                        "ingested_via": "source_registry_run",
                        "capture_mode": capture.capture_mode,
                        "capture_title": capture.title,
                        "matched_anchor_text": text,
                        "table_count": len(table_records),
                    },
                )
            )

        if candidates:
            return candidates

        fallback_text = self._clean_text(capture.title or source.display_name)
        return [
            ParsedScholarshipCandidate(
                source_key=source.source_key,
                source_display_name=source.display_name,
                source_base_url=source.base_url,
                source_type=source.source_type,
                title=fallback_text,
                provider_name=source.display_name,
                country_code=self._infer_country_code(source, capture.final_url),
                source_url=capture.final_url,
                summary=self._build_candidate_summary(fallback_text, page_summary or page_text[:300]),
                funding_summary=self._extract_funding_summary(f"{page_summary} {table_text}"),
                field_tags=self._infer_field_tags(f"{fallback_text} {page_summary} {page_text}") or ["data science"],
                degree_levels=self._infer_degree_levels(f"{fallback_text} {page_text}"),
                citizenship_rules=[],
                source_document_ref=self._slugify(fallback_text),
                imported_at=datetime.now(timezone.utc),
                source_last_seen_at=datetime.now(timezone.utc),
                review_notes="Auto-imported from source page fallback record; curator review required.",
                provenance_payload={
                    "ingested_via": "source_registry_run_fallback",
                    "capture_mode": capture.capture_mode,
                    "capture_title": capture.title,
                    "table_count": len(table_records),
                },
            )
        ]

    def _extract_table_records(self, html: str) -> list[list[dict[str, Any]]]:
        try:
            import pandas as pd

            frames = pd.read_html(StringIO(html))
        except ValueError:
            return []
        except Exception:
            return []

        tables: list[list[dict[str, Any]]] = []
        for frame in frames[:5]:
            if frame.empty:
                continue
            normalized = frame.fillna("").astype(str).head(12)
            tables.append(normalized.to_dict(orient="records"))
        return tables

    def _build_candidate_summary(self, title: str, page_summary: str | None) -> str:
        summary = page_summary.strip() if page_summary else ""
        if summary:
            summary = re.sub(r"\s+", " ", summary)[:350]
            return f"{title}. {summary}"
        return f"{title}. Imported from the approved source registry for curator review."

    def _extract_funding_summary(self, text: str) -> str | None:
        lowered = text.lower()
        for keyword in ("stipend", "tuition", "funding", "award", "grant"):
            if keyword in lowered:
                return f"Potential {keyword}-related support mentioned on the source page; curator verification required."
        return None

    def _infer_field_tags(self, text: str) -> list[str]:
        lowered = text.lower()
        matched = [
            canonical
            for canonical, keywords in FIELD_KEYWORD_MAP.items()
            if any(keyword in lowered for keyword in keywords)
        ]
        return matched

    def _infer_degree_levels(self, text: str) -> list[str]:
        lowered = text.lower()
        if any(keyword in lowered for keyword in DEGREE_KEYWORDS):
            return ["MS"]
        return ["MS"]

    def _infer_country_code(self, source: SourceRegistry, url: str) -> str:
        lowered = f"{source.source_key} {source.display_name} {url}".lower()
        if "fulbright" in lowered or "foreign.fulbright" in lowered:
            return "US"
        return "CA"

    def _looks_like_candidate(self, text: str) -> bool:
        lowered = text.lower()
        return any(keyword in lowered for keyword in SCHOLARSHIP_KEYWORDS)

    def _extract_title(self, html: str) -> str | None:
        match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return self._clean_text(match.group(1))

    def _extract_meta_description(self, soup: BeautifulSoup) -> str | None:
        meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"}
        )
        if not meta:
            return None
        content = meta.get("content")
        return self._clean_text(content) if content else None

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug[:255]

    def _resolve_run_status(
        self,
        records_found: int,
        records_created: int,
        records_skipped: int,
    ) -> IngestionRunStatus:
        if records_created > 0 and records_skipped == 0:
            return IngestionRunStatus.COMPLETED
        if records_created > 0 or records_found > 0 or records_skipped > 0:
            return IngestionRunStatus.PARTIAL
        return IngestionRunStatus.FAILED

    def _build_summary(self, run: IngestionRun) -> IngestionRunSummary:
        return IngestionRunSummary(
            run_id=str(run.id),
            source_key=run.source_registry.source_key,
            source_display_name=run.source_registry.display_name,
            fetch_url=run.fetch_url,
            status=run.status.value,
            capture_mode=run.capture_mode,
            parser_name=run.parser_name,
            records_found=run.records_found,
            records_created=run.records_created,
            records_skipped=run.records_skipped,
            failure_reason=run.failure_reason,
            started_at=run.started_at,
            completed_at=run.completed_at,
            created_at=run.created_at,
        )

    def _build_detail(self, run: IngestionRun) -> IngestionRunDetail:
        return IngestionRunDetail(
            **self._build_summary(run).model_dump(),
            run_metadata=run.run_metadata,
        )
