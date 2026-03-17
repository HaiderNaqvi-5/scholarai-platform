import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AuditLog, RecordState, Scholarship, SourceRegistry
from app.schemas.curation import (
    CurationActionRequest,
    CurationRawImportRequest,
    CurationRecordDetail,
    CurationRecordSummary,
    CurationRecordUpdateRequest,
)
from app.services.recommendations.hybrid_retriever import OpenSearchHybridRetriever


class CurationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.retriever = OpenSearchHybridRetriever()

    async def import_raw_record(
        self,
        payload: CurationRawImportRequest,
        actor_user_id: uuid.UUID,
    ) -> CurationRecordDetail:
        # Content-hash deduplication
        content_string = f"{payload.title}|{payload.summary or ''}|{payload.provider_name or ''}"
        content_hash = hashlib.sha256(content_string.encode()).hexdigest()
        
        existing_hash_result = await self.db.execute(
            select(Scholarship).where(Scholarship.content_hash == content_hash)
        )
        if existing_hash_result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A scholarship record with identical content already exists",
            )

        existing_url_result = await self.db.execute(
            select(Scholarship).where(Scholarship.source_url == str(payload.source_url))
        )
        if existing_url_result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A scholarship record already exists for this source URL",
            )

        source_registry = await self._get_or_create_source_registry(payload)
        timestamp = datetime.now(timezone.utc)

        record = Scholarship(
            source_registry=source_registry,
            external_source_id=payload.external_source_id,
            title=payload.title,
            provider_name=payload.provider_name,
            country_code=payload.country_code,
            summary=payload.summary,
            funding_summary=payload.funding_summary,
            source_url=str(payload.source_url),
            source_document_ref=payload.source_document_ref,
            field_tags=list(payload.field_tags),
            degree_levels=list(payload.degree_levels),
            citizenship_rules=list(payload.citizenship_rules),
            min_gpa_value=payload.min_gpa_value,
            deadline_at=payload.deadline_at,
            record_state=RecordState.RAW,
            content_hash=content_hash,
            imported_at=payload.imported_at or timestamp,
            provenance_payload=payload.provenance_payload or {},
            source_last_seen_at=payload.source_last_seen_at or payload.imported_at or timestamp,
            review_notes=payload.review_notes,
            reviewed_by_user_id=actor_user_id,
            last_reviewed_at=timestamp,
        )
        self.db.add(record)
        await self.db.flush()
        await self._append_audit_log(
            actor_user_id=actor_user_id,
            record=record,
            action="curation.import_raw",
            before={},
            after=self._snapshot(record),
        )
        await self.db.flush()
        return self._build_detail(record)

    async def list_records(
        self,
        state: str | None = None,
        limit: int = 50,
    ) -> list[CurationRecordSummary]:
        query = (
            select(Scholarship)
            .options(selectinload(Scholarship.source_registry))
            .order_by(Scholarship.updated_at.desc(), Scholarship.title.asc())
            .limit(limit)
        )

        if state:
            parsed_state = self._parse_state(state)
            query = query.where(Scholarship.record_state == parsed_state)

        result = await self.db.execute(query)
        return [self._build_summary(item) for item in result.scalars().all()]

    async def get_record(self, record_id: uuid.UUID) -> CurationRecordDetail:
        record = await self._load_record(record_id)
        return self._build_detail(record)

    async def update_record(
        self,
        record_id: uuid.UUID,
        payload: CurationRecordUpdateRequest,
        actor_user_id: uuid.UUID,
    ) -> CurationRecordDetail:
        record = await self._load_record(record_id)
        before = self._snapshot(record)
        values = payload.model_dump(exclude_unset=True)

        for field, value in values.items():
            setattr(record, field, value)

        record.reviewed_by_user_id = actor_user_id
        record.last_reviewed_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self._append_audit_log(
            actor_user_id=actor_user_id,
            record=record,
            action="curation.update",
            before=before,
            after=self._snapshot(record),
        )
        await self.db.flush()
        return self._build_detail(record)

    async def approve_record(
        self,
        record_id: uuid.UUID,
        payload: CurationActionRequest,
        actor_user_id: uuid.UUID,
    ) -> CurationRecordDetail:
        record = await self._load_record(record_id)
        if record.record_state != RecordState.RAW:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only raw records can be approved into validated state",
            )

        before = self._snapshot(record)
        timestamp = datetime.now(timezone.utc)
        record.record_state = RecordState.VALIDATED
        record.reviewed_by_user_id = actor_user_id
        record.validated_by_user_id = actor_user_id
        record.last_reviewed_at = timestamp
        record.validated_at = timestamp
        record.rejected_at = None
        record.unpublished_at = None
        if payload.note is not None:
            record.review_notes = payload.note

        await self.db.flush()
        await self._append_audit_log(
            actor_user_id=actor_user_id,
            record=record,
            action="curation.approve",
            before=before,
            after=self._snapshot(record),
        )
        await self.db.flush()
        return self._build_detail(record)

    async def reject_record(
        self,
        record_id: uuid.UUID,
        payload: CurationActionRequest,
        actor_user_id: uuid.UUID,
    ) -> CurationRecordDetail:
        record = await self._load_record(record_id)
        if record.record_state not in {RecordState.RAW, RecordState.VALIDATED}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only raw or validated records can be rejected",
            )

        before = self._snapshot(record)
        timestamp = datetime.now(timezone.utc)
        record.record_state = RecordState.ARCHIVED
        record.reviewed_by_user_id = actor_user_id
        record.last_reviewed_at = timestamp
        record.rejected_at = timestamp
        record.unpublished_at = None
        if payload.note is not None:
            record.review_notes = payload.note

        await self.db.flush()
        await self._append_audit_log(
            actor_user_id=actor_user_id,
            record=record,
            action="curation.reject",
            before=before,
            after=self._snapshot(record),
        )
        await self.db.flush()
        return self._build_detail(record)

    async def publish_record(
        self,
        record_id: uuid.UUID,
        payload: CurationActionRequest,
        actor_user_id: uuid.UUID,
    ) -> CurationRecordDetail:
        record = await self._load_record(record_id)
        if record.record_state != RecordState.VALIDATED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only validated records can be published",
            )

        before = self._snapshot(record)
        timestamp = datetime.now(timezone.utc)
        record.record_state = RecordState.PUBLISHED
        record.reviewed_by_user_id = actor_user_id
        record.last_reviewed_at = timestamp
        record.published_by_user_id = actor_user_id
        record.published_at = timestamp
        record.unpublished_at = None
        if payload.note is not None:
            record.review_notes = payload.note

        await self.db.flush()
        
        # Trigger OpenSearch indexing
        try:
            # We need an embedding for the scholarship. 
            # In a real system, this would be a background task.
            embedding = [0.0] * 768 # Placeholder for MVP
            await self.retriever.index_scholarship(record, embedding)
        except Exception as e:
            print(f"Failed to index scholarship into OpenSearch: {e}")
            
        return self._build_detail(record)

    async def unpublish_record(
        self,
        record_id: uuid.UUID,
        payload: CurationActionRequest,
        actor_user_id: uuid.UUID,
    ) -> CurationRecordDetail:
        record = await self._load_record(record_id)
        if record.record_state != RecordState.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only published records can be unpublished",
            )

        before = self._snapshot(record)
        timestamp = datetime.now(timezone.utc)
        record.record_state = RecordState.VALIDATED
        record.reviewed_by_user_id = actor_user_id
        record.last_reviewed_at = timestamp
        record.unpublished_at = timestamp
        if payload.note is not None:
            record.review_notes = payload.note

        await self.db.flush()
        
        # Remove from OpenSearch index
        try:
            await self.retriever.delete_scholarship(str(record.id))
        except Exception as e:
            print(f"Failed to remove scholarship from OpenSearch: {e}")
            
        return self._build_detail(record)

    async def _load_record(self, record_id: uuid.UUID) -> Scholarship:
        result = await self.db.execute(
            select(Scholarship)
            .where(Scholarship.id == record_id)
            .options(selectinload(Scholarship.source_registry))
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Curation record not found",
            )
        return record

    async def _get_or_create_source_registry(
        self,
        payload: CurationRawImportRequest,
    ) -> SourceRegistry:
        result = await self.db.execute(
            select(SourceRegistry).where(SourceRegistry.source_key == payload.source_key)
        )
        source_registry = result.scalar_one_or_none()
        if source_registry is None:
            source_registry = SourceRegistry(
                source_key=payload.source_key,
                display_name=payload.source_display_name,
                base_url=str(payload.source_base_url),
                source_type=payload.source_type,
                is_active=True,
            )
            self.db.add(source_registry)
            await self.db.flush()
            return source_registry

        source_registry.display_name = payload.source_display_name
        source_registry.base_url = str(payload.source_base_url)
        source_registry.source_type = payload.source_type
        source_registry.is_active = True
        return source_registry

    async def _append_audit_log(
        self,
        actor_user_id: uuid.UUID,
        record: Scholarship,
        action: str,
        before: dict,
        after: dict,
    ) -> None:
        audit = AuditLog(
            actor_user_id=actor_user_id,
            entity_type="scholarship",
            entity_id=str(record.id),
            action=action,
            before_data=before,
            after_data=after,
        )
        self.db.add(audit)

    def _build_summary(self, record: Scholarship) -> CurationRecordSummary:
        source_type = record.source_registry.source_type if record.source_registry else None
        return CurationRecordSummary(
            record_id=str(record.id),
            title=record.title,
            provider_name=record.provider_name,
            country_code=record.country_code,
            record_state=record.record_state.value,
            source_url=record.source_url,
            source_type=source_type,
            imported_at=record.imported_at,
            source_last_seen_at=record.source_last_seen_at,
            last_reviewed_at=record.last_reviewed_at,
            validated_at=record.validated_at,
            published_at=record.published_at,
            review_notes=record.review_notes,
        )

    def _build_detail(self, record: Scholarship) -> CurationRecordDetail:
        return CurationRecordDetail(
            **self._build_summary(record).model_dump(),
            summary=record.summary,
            funding_summary=record.funding_summary,
            field_tags=record.field_tags,
            degree_levels=record.degree_levels,
            citizenship_rules=record.citizenship_rules,
            min_gpa_value=float(record.min_gpa_value) if record.min_gpa_value is not None else None,
            source_document_ref=record.source_document_ref,
            provenance_payload=record.provenance_payload,
            reviewed_by_user_id=str(record.reviewed_by_user_id) if record.reviewed_by_user_id else None,
            validated_by_user_id=str(record.validated_by_user_id) if record.validated_by_user_id else None,
            published_by_user_id=str(record.published_by_user_id) if record.published_by_user_id else None,
            rejected_at=record.rejected_at,
            unpublished_at=record.unpublished_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _parse_state(self, value: str) -> RecordState:
        try:
            return RecordState(value.lower())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State must be one of raw, validated, published, or archived",
            ) from exc

    def _snapshot(self, record: Scholarship) -> dict:
        source_type = record.source_registry.source_type if record.source_registry else None
        return {
            "record_state": record.record_state.value,
            "title": record.title,
            "provider_name": record.provider_name,
            "country_code": record.country_code,
            "source_url": record.source_url,
            "source_type": source_type,
            "review_notes": record.review_notes,
            "validated_at": record.validated_at.isoformat() if record.validated_at else None,
            "published_at": record.published_at.isoformat() if record.published_at else None,
            "rejected_at": record.rejected_at.isoformat() if record.rejected_at else None,
            "unpublished_at": record.unpublished_at.isoformat() if record.unpublished_at else None,
        }
