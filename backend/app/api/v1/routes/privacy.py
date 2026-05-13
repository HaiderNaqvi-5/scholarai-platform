"""Privacy + consent + legal-document REST surface (Feature 9.5, PRD §9.5)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.consent import (
    ALLOWED_CONSENT_TYPES,
    get_current_legal_doc,
    latest_consent,
    record_consent,
)
from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.models import LegalDocument
from app.schemas.privacy import (
    ConsentGrantRequest,
    ConsentRecordResponse,
    ConsentStateResponse,
    DataDeletionCreateRequest,
    DataDeletionRequestResponse,
    DataExportResponse,
    LegalDocumentResponse,
)
from app.services.privacy import DeletionService, ExportService


router = APIRouter()


# ---------------------------------------------------------------------
# Consent
# ---------------------------------------------------------------------


@router.post("/consent", response_model=ConsentStateResponse)
async def grant_consent(
    payload: ConsentGrantRequest,
    request: Request,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConsentStateResponse:
    doc = await get_current_legal_doc(db, payload.consent_type) if payload.consent_type in {
        "terms", "privacy", "cookies", "b2b_data_use", "aup"
    } else None
    document_sha256 = doc.sha256_hash if doc else None
    await record_consent(
        db,
        current_user,
        consent_type=payload.consent_type,
        version=payload.version,
        granted=payload.granted,
        request=request,
        document_sha256=document_sha256,
    )
    return await _build_consent_state(db, current_user.id)


@router.get("/consent", response_model=ConsentStateResponse)
async def get_consent_state(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConsentStateResponse:
    return await _build_consent_state(db, current_user.id)


async def _build_consent_state(db: AsyncSession, user_id: uuid.UUID) -> ConsentStateResponse:
    records = []
    for consent_type in sorted(ALLOWED_CONSENT_TYPES):
        record = await latest_consent(db, user_id, consent_type)
        if record is not None:
            records.append(
                ConsentRecordResponse(
                    consent_type=record.consent_type,
                    version=record.version,
                    granted=record.granted,
                    granted_at=record.granted_at,
                )
            )
    versions: dict[str, str] = {}
    docs = await db.execute(
        select(LegalDocument).where(LegalDocument.is_current.is_(True))
    )
    for doc in docs.scalars().all():
        versions[doc.slug] = doc.version
    return ConsentStateResponse(records=records, current_versions=versions)


# ---------------------------------------------------------------------
# Legal documents
# ---------------------------------------------------------------------


@router.get("/legal/{slug}", response_model=LegalDocumentResponse)
async def get_legal_document(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LegalDocumentResponse:
    doc = await get_current_legal_doc(db, slug)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return LegalDocumentResponse(
        slug=doc.slug,
        version=doc.version,
        effective_at=doc.effective_at,
        body_markdown=doc.body_markdown,
        sha256_hash=doc.sha256_hash,
    )


# ---------------------------------------------------------------------
# Data export
# ---------------------------------------------------------------------


@router.post("/data-export", response_model=DataExportResponse, status_code=status.HTTP_201_CREATED)
async def request_data_export(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DataExportResponse:
    service = ExportService(db)
    record = await service.request_export(current_user)
    # For demo / SLC fulfilment we run the export inline. Production wires this
    # to a Celery task that uploads to signed S3 storage.
    fulfilled = await service.fulfil_export(record.id)
    return DataExportResponse(
        id=fulfilled.id if fulfilled else record.id,
        status=fulfilled.status if fulfilled else record.status,
        requested_at=record.requested_at,
        completed_at=fulfilled.completed_at if fulfilled else None,
        download_url=fulfilled.download_url if fulfilled else None,
        expires_at=fulfilled.expires_at if fulfilled else None,
    )


@router.get("/data-export/{request_id}", response_model=DataExportResponse)
async def get_data_export_status(
    request_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DataExportResponse:
    from app.models import DataExportRequest as _ExportModel  # local import keeps blast radius small

    record = await db.get(_ExportModel, request_id)
    if record is None or record.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    return DataExportResponse(
        id=record.id,
        status=record.status,
        requested_at=record.requested_at,
        completed_at=record.completed_at,
        download_url=record.download_url,
        expires_at=record.expires_at,
    )


# ---------------------------------------------------------------------
# Account deletion (30-day window)
# ---------------------------------------------------------------------


@router.post(
    "/account-deletion",
    response_model=DataDeletionRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def schedule_account_deletion(
    payload: DataDeletionCreateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DataDeletionRequestResponse:
    service = DeletionService(db)
    record = await service.schedule(current_user, reason=payload.reason)
    return _serialise_deletion(record)


@router.delete(
    "/account-deletion",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_account_deletion(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = DeletionService(db)
    cancelled = await service.cancel(current_user.id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending deletion request found",
        )


def _serialise_deletion(record) -> DataDeletionRequestResponse:
    return DataDeletionRequestResponse(
        id=record.id,
        status=record.status,
        requested_at=record.requested_at,
        scheduled_for=record.scheduled_for,
        cancelled_at=record.cancelled_at,
        executed_at=record.executed_at,
    )
