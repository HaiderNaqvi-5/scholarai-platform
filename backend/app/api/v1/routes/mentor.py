"""
Mentor-specific document review endpoints.

Mentors can view all pending SOPs submitted by students and provide
human feedback on individual documents.
"""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import MentorReviewUser
from app.models import (
    DocumentFeedback,
    DocumentProcessingStatus,
    DocumentRecord,
)
from app.schemas.documents import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentRecordSummary,
)
from app.schemas.mentor import MentorFeedbackRequest, MentorFeedbackResponse
from app.services.documents.service import DocumentService

router = APIRouter()

HUMAN_MENTOR_LIMITATION_NOTICE = "Reviewed by a human mentor."


@router.get("/pending-reviews", response_model=DocumentListResponse)
async def list_pending_reviews(
    current_user: MentorReviewUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
) -> DocumentListResponse:
    """Return all student documents awaiting mentor review."""
    candidate_limit = min(limit * 4, 400)
    result = await db.execute(
        select(DocumentRecord)
        .where(DocumentRecord.processing_status == DocumentProcessingStatus.COMPLETED)
        .options(selectinload(DocumentRecord.feedback_entries))
        .order_by(DocumentRecord.created_at.desc())
        .limit(candidate_limit)
    )
    candidate_documents = result.scalars().all()

    items: list[DocumentRecordSummary] = []
    for doc in candidate_documents:
        has_human_review = any(
            (entry.limitation_notice or "").startswith(HUMAN_MENTOR_LIMITATION_NOTICE)
            for entry in doc.feedback_entries
        )
        if has_human_review:
            continue

        latest_fb_at = None
        if doc.feedback_entries:
            latest_fb_at = max(
                (entry.completed_at or entry.created_at) for entry in doc.feedback_entries
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
        if len(items) >= limit:
            break

    return DocumentListResponse(items=items, total=len(items))


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document_for_review(
    document_id: uuid.UUID,
    current_user: MentorReviewUser,
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
            key=lambda entry: entry.completed_at or entry.created_at,
            reverse=True,
        )
        latest_fb = DocumentService(db)._build_feedback(sorted_entries[0])

    return DocumentDetailResponse(
        id=str(document.id),
        title=document.title or "",
        document_type=document.document_type.value,
        input_method=document.input_method.value,
        processing_status=document.processing_status.value,
        original_filename=document.original_filename,
        created_at=document.created_at,
        updated_at=document.updated_at,
        latest_feedback_at=latest_fb.completed_at if latest_fb else document.latest_feedback_at,
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
    current_user: MentorReviewUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MentorFeedbackResponse:
    """Submit human mentor feedback on a student document."""
    result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    completed_at = datetime.now(timezone.utc)
    feedback_payload = {
        "summary": payload.summary.strip(),
        "strengths": [item.strip() for item in payload.strengths if item.strip()],
        "revision_priorities": [
            item.strip() for item in payload.revision_priorities if item.strip()
        ],
        "caution_notes": [item.strip() for item in payload.caution_notes if item.strip()],
        "citations": [],
        "grounded_context": [],
        "grounded_context_sections": {
            "validated_facts": [],
            "retrieved_writing_guidance": [],
            "generated_guidance": [
                {
                    "type": "mentor_feedback",
                    "guidance": "Human mentor review provided for this draft.",
                }
            ],
            "limitations": [HUMAN_MENTOR_LIMITATION_NOTICE],
        },
    }

    feedback = DocumentFeedback(
        document_id=document.id,
        status=DocumentProcessingStatus.COMPLETED,
        feedback_payload=feedback_payload,
        limitation_notice=HUMAN_MENTOR_LIMITATION_NOTICE,
        completed_at=completed_at,
    )
    db.add(feedback)
    document.latest_feedback_at = completed_at
    await db.flush()
    await db.commit()
    await db.refresh(feedback)

    return MentorFeedbackResponse(
        id=str(feedback.id),
        document_id=str(document.id),
        mentor_id=str(current_user.id),
        summary=feedback_payload["summary"],
        strengths=feedback_payload["strengths"],
        revision_priorities=feedback_payload["revision_priorities"],
        caution_notes=feedback_payload["caution_notes"],
        submitted_at=feedback.completed_at,
    )
