"""
Mentor-specific document review endpoints.

Mentors can view all pending SOPs submitted by students and provide
human feedback on individual documents.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import MentorUser
from app.models import (
    DocumentFeedback,
    DocumentProcessingStatus,
    DocumentRecord,
    User,
)
from app.schemas.documents import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentRecordSummary,
)
from app.schemas.mentor import MentorFeedbackRequest, MentorFeedbackResponse

router = APIRouter()


@router.get("/pending-reviews", response_model=DocumentListResponse)
async def list_pending_reviews(
    current_user: MentorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
) -> DocumentListResponse:
    """Return all student documents awaiting mentor review."""
    result = await db.execute(
        select(DocumentRecord)
        .where(DocumentRecord.processing_status == DocumentProcessingStatus.COMPLETED)
        .options(selectinload(DocumentRecord.feedback_entries))
        .order_by(DocumentRecord.created_at.desc())
        .limit(limit)
    )
    documents = result.scalars().all()

    items: list[DocumentRecordSummary] = []
    for doc in documents:
        latest_fb_at = None
        if doc.feedback_entries:
            latest_fb_at = max(
                fb.completed_at for fb in doc.feedback_entries if fb.completed_at
            )
        items.append(
            DocumentRecordSummary(
                id=str(doc.id),
                title=doc.title or "",
                document_type=doc.document_type.value,
                input_method=doc.input_method.value,
                processing_status=doc.processing_status.value,
                original_filename=doc.original_filename,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                latest_feedback_at=latest_fb_at,
            )
        )

    return DocumentListResponse(items=items, total=len(items))


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document_for_review(
    document_id: uuid.UUID,
    current_user: MentorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentDetailResponse:
    """Fetch a single student document for mentor review."""
    result = await db.execute(
        select(DocumentRecord)
        .where(DocumentRecord.id == document_id)
        .options(selectinload(DocumentRecord.feedback_entries))
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    latest_fb = None
    if document.feedback_entries:
        sorted_entries = sorted(
            document.feedback_entries,
            key=lambda fb: fb.completed_at or fb.created_at,
            reverse=True,
        )
        entry = sorted_entries[0]
        from app.schemas.documents import DocumentFeedbackResponse

        latest_fb = DocumentFeedbackResponse(
            id=str(entry.id),
            status=entry.status,
            summary=entry.summary or "",
            strengths=entry.strengths or [],
            revision_priorities=entry.revision_priorities or [],
            caution_notes=entry.caution_notes or [],
            citations=entry.citations or [],
            grounded_context=entry.grounded_context or [],
            limitation_notice=entry.limitation_notice or "",
            completed_at=entry.completed_at,
        )

    return DocumentDetailResponse(
        id=str(document.id),
        title=document.title or "",
        document_type=document.document_type.value,
        input_method=document.input_method.value,
        processing_status=document.processing_status.value,
        original_filename=document.original_filename,
        created_at=document.created_at,
        updated_at=document.updated_at,
        latest_feedback_at=latest_fb.completed_at if latest_fb else None,
        content_text=document.content_text or "",
        latest_feedback=latest_fb,
    )


@router.post(
    "/documents/{document_id}/feedback",
    response_model=MentorFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_mentor_feedback(
    document_id: uuid.UUID,
    payload: MentorFeedbackRequest,
    current_user: MentorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MentorFeedbackResponse:
    """Submit human mentor feedback on a student document."""
    result = await db.execute(
        select(DocumentRecord).where(DocumentRecord.id == document_id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    from datetime import datetime, timezone

    feedback = DocumentFeedback(
        document_id=document.id,
        status="completed",
        summary=payload.summary,
        strengths=payload.strengths,
        revision_priorities=payload.revision_priorities,
        caution_notes=payload.caution_notes or [],
        citations=[],
        grounded_context=[],
        limitation_notice="Reviewed by a human mentor.",
        completed_at=datetime.now(timezone.utc),
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return MentorFeedbackResponse(
        id=str(feedback.id),
        document_id=str(document.id),
        mentor_id=str(current_user.id),
        summary=feedback.summary or "",
        strengths=feedback.strengths or [],
        revision_priorities=feedback.revision_priorities or [],
        caution_notes=feedback.caution_notes or [],
        submitted_at=feedback.completed_at,
    )
