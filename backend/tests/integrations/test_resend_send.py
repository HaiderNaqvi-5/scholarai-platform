import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from app.integrations.resend.send import send_transactional, TransactionalRequest


def test_rejects_crlf_in_email(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    with pytest.raises(ValidationError):
        TransactionalRequest(
            to="victim@x.com\r\nBcc: attacker@y.com",
            template="welcome",
            context={"name": "x"},
        )


def test_rejects_unknown_template(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    with pytest.raises(ValidationError):
        TransactionalRequest(
            to="v@x.com", template="not_a_real_template", context={},
        )


@patch("app.integrations.resend.send.resend")
def test_send_calls_resend_with_params(mock_resend, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("RESEND_FROM_ADDRESS", "noreply@grantpath.app")
    mock_resend.Emails.send.return_value = MagicMock(id="msg_123")
    result = send_transactional(
        to="user@x.com", template="welcome", context={"name": "Alice"},
    )
    assert result == "msg_123"
    args = mock_resend.Emails.send.call_args[0][0]
    assert args["to"] == ["user@x.com"]
    assert args["from"] == "noreply@grantpath.app"
    assert "Alice" in args["html"]
