import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import DocumentCreateUser, DocumentFeedbackUser, DocumentReadUser
from app.schemas import (
    DocumentDetailResponse,
    DocumentFeedbackRefreshResponse,
    DocumentListResponse,
    DocumentSubmissionResponse,
)
from app.schemas.professor_email import ProfessorEmailRequest, ProfessorEmailResponse
from app.schemas.sop import SOPDraftRequest, SOPDraftResponse
from app.services.documents import DocumentService
from app.services.documents.professor_email import ProfessorEmailService
from app.services.documents.sop_builder import SOPBuilderService

router = APIRouter()


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    current_user: DocumentReadUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentListResponse:
    service = DocumentService(db)
    items = await service.list_documents(current_user.id)
    return DocumentListResponse(items=items, total=len(items))


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: DocumentReadUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentDetailResponse:
    service = DocumentService(db)
    return await service.get_document(current_user.id, document_id)


@router.post("/sop/draft", response_model=SOPDraftResponse, status_code=status.HTTP_201_CREATED)
async def generate_sop_draft(
    payload: SOPDraftRequest,
    current_user: DocumentCreateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SOPDraftResponse:
    """Pakistan-context SOP builder (PRD §7).

    Free tier is gated to one SOP per account; Elite tier receives line-by-line
    paragraph feedback alongside the draft. Persists the generated draft as a
    DocumentRecord so it shows up in GET /documents and /documents/{id}.
    """
    service = SOPBuilderService(db)
    return await service.draft(current_user, payload)


@router.post(
    "/professor-email",
    response_model=ProfessorEmailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_professor_email(
    payload: ProfessorEmailRequest,
    current_user: DocumentCreateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfessorEmailResponse:
    """Elite professor cold-email generator (PRD §0.6).

    Gated to elite + institution plans — returns HTTP 402 otherwise. Persists
    the generated email as a DocumentRecord so it shows up in GET /documents.
    """
    service = ProfessorEmailService(db)
    return await service.generate(current_user, payload)


@router.post("", response_model=DocumentSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    current_user: DocumentCreateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    document_type: Annotated[str, Form(...)],
    title: Annotated[str | None, Form()] = None,
    content_text: Annotated[str | None, Form()] = None,
    scholarship_id: Annotated[str | None, Form()] = None,
    scholarship_ids: Annotated[list[str] | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
) -> DocumentSubmissionResponse:
    service = DocumentService(db)
    document = await service.submit_document(
        user_id=current_user.id,
        document_type=document_type,
        title=title,
        content_text=content_text,
        scholarship_id=scholarship_id,
        scholarship_ids=scholarship_ids,
        upload=file,
    )
    return DocumentSubmissionResponse(document=document)


@router.post(
    "/{document_id}/feedback",
    response_model=DocumentFeedbackRefreshResponse,
)
async def request_document_feedback(
    document_id: uuid.UUID,
    current_user: DocumentFeedbackUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentFeedbackRefreshResponse:
    service = DocumentService(db)
    document = await service.regenerate_feedback(current_user.id, document_id)
    return DocumentFeedbackRefreshResponse(document=document)
