"""P2-15: upload size + text/list field-length caps on POST /documents.

Mirrors the harness style of test_document_feedback_grounded_flow.py — sync
TestClient, dummy current_user + no-op db dependency overrides, and a
DocumentService.submit_document monkeypatch used as a tripwire: if the
monkeypatch fires, the request reached the service layer, meaning the cap
did NOT reject the request before hitting the DB. These tests need no
Postgres, so they always run offline.
"""

import io
from uuid import uuid4

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import UserRole
from app.services.documents.service import MAX_FILE_SIZE_BYTES, MAX_TEXT_LENGTH


class _DummyCurrentUser:
    def __init__(self):
        self.id = uuid4()
        self.role = UserRole.STUDENT
        self._token_capabilities = {
            "document.self.create",
            "document.self.read",
            "document.self.feedback",
        }


class _NoOpDB:
    async def execute(self, _query):
        return None

    def add(self, _value):
        return None

    async def flush(self):
        return None

    async def refresh(self, _value):
        return None


def _install_overrides(app):
    current_user = _DummyCurrentUser()
    db = _NoOpDB()

    async def override_current_user():
        return current_user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    return current_user


def _install_tripwire(monkeypatch):
    """Fail loudly if the request reaches DocumentService.submit_document.

    A 422/413 rejection must happen before the service/DB is ever touched.
    """
    from app.services.documents.service import DocumentService

    async def fake_submit_document(self, *args, **kwargs):
        raise AssertionError(
            "DocumentService.submit_document was called — the cap did not "
            "reject the request before hitting the service/DB layer"
        )

    monkeypatch.setattr(DocumentService, "submit_document", fake_submit_document)


def test_oversized_document_type_rejected_422(app, client, monkeypatch):
    _install_overrides(app)
    _install_tripwire(monkeypatch)

    response = client.post(
        "/api/v1/documents",
        data={
            "document_type": "x" * 65,
            "content_text": "a" * 60,
        },
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 422


def test_oversized_title_rejected_422(app, client, monkeypatch):
    _install_overrides(app)
    _install_tripwire(monkeypatch)

    response = client.post(
        "/api/v1/documents",
        data={
            "document_type": "sop",
            "title": "t" * 256,
            "content_text": "a" * 60,
        },
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 422


def test_oversized_content_text_rejected_422(app, client, monkeypatch):
    _install_overrides(app)
    _install_tripwire(monkeypatch)

    response = client.post(
        "/api/v1/documents",
        data={
            "document_type": "sop",
            "content_text": "a" * (MAX_TEXT_LENGTH + 1),
        },
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 422


def test_too_many_scholarship_ids_rejected_422(app, client, monkeypatch):
    _install_overrides(app)
    _install_tripwire(monkeypatch)

    response = client.post(
        "/api/v1/documents",
        data={
            "document_type": "sop",
            "content_text": "a" * 60,
            "scholarship_ids": [str(uuid4()) for _ in range(4)],
        },
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 422


def test_oversized_upload_rejected_413(app, client, monkeypatch):
    _install_overrides(app)
    _install_tripwire(monkeypatch)

    oversized_payload = b"a" * (MAX_FILE_SIZE_BYTES + 1)

    response = client.post(
        "/api/v1/documents",
        data={"document_type": "sop"},
        files={"file": ("draft.txt", io.BytesIO(oversized_payload), "text/plain")},
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 413
