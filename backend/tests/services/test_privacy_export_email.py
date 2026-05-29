"""Verify ExportService.fulfil_export dispatches a data_export_ready email."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.services.privacy import export_service as export_module
from app.services.privacy.export_service import ExportService


class _FakeAsyncDB:
    """Minimal async DB stub for ExportService.fulfil_export."""

    def __init__(self, request, user):
        self._request = request
        self._user = user

    async def get(self, model, pk):
        # ExportService calls .get twice: DataExportRequest then User.
        name = model.__name__
        if name == "DataExportRequest":
            return self._request
        if name == "User":
            return self._user
        return None

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_fulfil_export_sends_data_export_ready_email(monkeypatch, tmp_path):
    user = SimpleNamespace(
        id=uuid.uuid4(),
        email="exp@example.com",
        full_name="Exp User",
        role=None,
        plan="free",
        plan_currency=None,
        billing_country=None,
        marketing_consent=False,
        b2b_share_consent=False,
        account_deleted_at=None,
        created_at=None,
    )
    request = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user.id,
        status="pending",
        completed_at=None,
        download_url=None,
        expires_at=None,
    )

    # Redirect bundle output into pytest's tmp_path so we don't touch the
    # backend/runtime/exports directory.
    monkeypatch.setattr(export_module, "EXPORT_ROOT", tmp_path)

    # Stub the fetch helpers so we don't need real ORM queries.
    monkeypatch.setattr(ExportService, "_fetch_profile", lambda self, uid: _async_none())
    monkeypatch.setattr(ExportService, "_fetch_tracker", lambda self, uid: _async_list())
    monkeypatch.setattr(ExportService, "_fetch_documents", lambda self, uid: _async_list())
    monkeypatch.setattr(ExportService, "_fetch_interviews", lambda self, uid: _async_list())
    monkeypatch.setattr(ExportService, "_fetch_consent_log", lambda self, uid: _async_list())

    sent: list[dict] = []

    def fake_send(*, to, template, context, source):
        sent.append({"to": to, "template": template, "context": context, "source": source})
        return "msg_export_ok"

    monkeypatch.setattr(export_module, "send_templated_email_best_effort", fake_send)

    db = _FakeAsyncDB(request, user)
    svc = ExportService(db)
    result = await svc.fulfil_export(request.id)

    assert result.status == "completed"
    assert result.download_url and result.download_url.startswith("file:")
    assert len(sent) == 1
    assert sent[0]["to"] == "exp@example.com"
    assert sent[0]["template"] == "data_export_ready"
    assert sent[0]["source"] == "data_export"
    assert sent[0]["context"]["name"] == "Exp User"
    assert sent[0]["context"]["download_url"] == result.download_url


async def _async_none():
    return None


async def _async_list():
    return []
