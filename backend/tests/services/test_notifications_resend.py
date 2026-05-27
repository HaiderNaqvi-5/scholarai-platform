from unittest.mock import patch

from app.services.notifications import channels
from app.services.notifications.channels import (
    send_email_notification,
    send_templated_email_best_effort,
)


@patch("app.services.notifications.channels.send_transactional")
def test_email_notification_routes_to_resend(mock_send):
    mock_send.return_value = "msg_xyz"
    msg_id = send_email_notification(
        to="user@x.com", template="welcome", context={"name": "Alice"},
    )
    assert msg_id == "msg_xyz"
    mock_send.assert_called_once_with(
        to="user@x.com", template="welcome", context={"name": "Alice"},
    )


def test_best_effort_returns_id_on_success(monkeypatch):
    monkeypatch.setattr(
        channels, "send_email_notification",
        lambda **_: "msg_ok",
    )
    result = send_templated_email_best_effort(
        to="x@y.com", template="welcome", context={}, source="welcome",
    )
    assert result == "msg_ok"


def test_best_effort_swallows_resend_error(monkeypatch, caplog):
    def boom(**_):
        raise RuntimeError("resend down")

    monkeypatch.setattr(channels, "send_email_notification", boom)
    with caplog.at_level("WARNING"):
        result = send_templated_email_best_effort(
            to="x@y.com", template="welcome", context={}, source="welcome",
        )
    assert result is None
    assert "welcome failed" in caplog.text
