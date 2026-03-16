import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas import (
    DocumentDetailResponse,
    DocumentFeedbackRefreshResponse,
    DocumentListResponse,
    DocumentSubmissionResponse,
)
from app.services.documents import DocumentService

router = APIRouter()


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentListResponse:
    service = DocumentService(db)
    items = await service.list_documents(current_user.id)
    return DocumentListResponse(items=items, total=len(items))


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentDetailResponse:
    service = DocumentService(db)
    return await service.get_document(current_user.id, document_id)


@router.post("", response_model=DocumentSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    document_type: Annotated[str, Form(...)],
    title: Annotated[str | None, Form()] = None,
    content_text: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
) -> DocumentSubmissionResponse:
    service = DocumentService(db)
    document = await service.submit_document(
        user_id=current_user.id,
        document_type=document_type,
        title=title,
        content_text=content_text,
        upload=file,
    )
    return DocumentSubmissionResponse(document=document)


@router.post(
    "/{document_id}/feedback",
    response_model=DocumentFeedbackRefreshResponse,
)
async def request_document_feedback(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentFeedbackRefreshResponse:
    service = DocumentService(db)
    document = await service.regenerate_feedback(current_user.id, document_id)
    return DocumentFeedbackRefreshResponse(document=document)
