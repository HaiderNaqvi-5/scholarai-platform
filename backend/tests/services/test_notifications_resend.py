from unittest.mock import patch

from app.services.notifications.channels import send_email_notification


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
