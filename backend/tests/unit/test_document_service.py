from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.models import DocumentType
from app.services.documents import DocumentService

pytestmark = pytest.mark.asyncio


class FakeSession:
    def __init__(self):
        self.added = []

    async def execute(self, _query):
        raise AssertionError("execute should not be called in this unit path")

    def add(self, value):
        if getattr(value, "id", None) is None:
            value.id = uuid4()
        if getattr(value, "created_at", None) is None:
            value.created_at = datetime.now(timezone.utc)
        if getattr(value, "updated_at", None) is None:
            value.updated_at = datetime.now(timezone.utc)
        self.added.append(value)

    async def flush(self):
        return None

    async def refresh(self, _value):
        return None


async def test_document_service_submit_text_generates_feedback():
    session = FakeSession()
    service = DocumentService(session)

    async def fake_load_document(user_id, document_id):
        document = session.added[0]
        feedback = session.added[1]
        document.feedback_entries = [feedback]
        document.id = document_id
        document.user_id = user_id
        return document

    service._load_document = fake_load_document  # type: ignore[method-assign]

    result = await service.submit_document(
        user_id=uuid4(),
        document_type="sop",
        title="Graduate SOP",
        content_text=(
            "I want to pursue graduate study in data science because my research "
            "projects and community work showed me how applied analytics can "
            "improve public services. I led a capstone project, learned from it, "
            "and now want a program that deepens both technical depth and impact."
        ),
    )

    assert result.processing_status == "completed"
    assert result.latest_feedback is not None
    assert result.latest_feedback.status == "completed"
    assert "validated scholarship records" in result.latest_feedback.limitation_notice
    assert len(session.added) == 2


async def test_document_service_rejects_unsupported_file_types():
    session = FakeSession()
    service = DocumentService(session)

    upload = UploadFile(
        file=BytesIO(b"Not a valid document format"),
        filename="draft.pdf",
        headers=Headers({"content-type": "application/pdf"}),
    )

    with pytest.raises(HTTPException) as caught:
        await service.submit_document(
            user_id=uuid4(),
            document_type=DocumentType.ESSAY.value,
            title="Essay upload",
            upload=upload,
        )

    assert caught.value.status_code == 400
    assert "plain-text" in str(caught.value.detail)
