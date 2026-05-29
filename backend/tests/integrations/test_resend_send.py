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
    # resend 2.5.1 returns a dict, not an object — mock the real shape so the
    # send.py response["id"] path is exercised (was masked by MagicMock(id=...)).
    mock_resend.Emails.send.return_value = {"id": "msg_123"}
    result = send_transactional(
        to="user@x.com", template="welcome", context={"name": "Alice"},
    )
    assert result == "msg_123"
    args = mock_resend.Emails.send.call_args[0][0]
    assert args["to"] == ["user@x.com"]
    assert args["from"] == "noreply@grantpath.app"
    assert "Alice" in args["html"]
    assert "AidwiseAI" in args["html"]


def test_welcome_template_has_aidwiseai_branding():
    from app.integrations.resend.templates.welcome import render
    subject, html, text = render({"name": "Alice", "login_url": "https://aidwiseai.com/login"})
    assert subject == "Welcome to AidwiseAI"
    assert "AidwiseAI" in html and "Alice" in html
    assert "https://aidwiseai.com/login" in html
    assert "GrantPath" not in html and "GrantPath" not in text
    assert "AidwiseAI" in text


def test_welcome_template_omits_cta_when_no_login_url():
    from app.integrations.resend.templates.welcome import render
    subject, html, text = render({"name": "Bob"})
    assert "Open AidwiseAI" not in html
    assert "Open AidwiseAI" not in text


def test_data_export_template_has_aidwiseai_branding():
    from app.integrations.resend.templates.data_export_ready import render
    subject, html, text = render({"name": "Alice", "download_url": "https://x/dl"})
    assert "AidwiseAI" in subject and "Alice" in html
    assert "https://x/dl" in html and "24" in text
    assert "GrantPath" not in html and "GrantPath" not in text


def test_account_deletion_scheduled_template():
    from app.integrations.resend.templates.account_deletion_scheduled import render
    subject, html, text = render({
        "name": "Carol",
        "scheduled_deletion_at": "2026-06-26",
        "cancel_url": "https://aidwiseai.com/settings/privacy",
    })
    assert "AidwiseAI" in subject and "Carol" in html
    assert "2026-06-26" in html and "2026-06-26" in text
    assert "https://aidwiseai.com/settings/privacy" in html
    assert "30 days" in html


def test_account_deletion_cancelled_template():
    from app.integrations.resend.templates.account_deletion_cancelled import render
    subject, html, text = render({"name": "Dave"})
    assert "cancelled" in subject and "Dave" in html
    assert "AidwiseAI" in html and "AidwiseAI" in text


def test_waitlist_confirmation_template():
    from app.integrations.resend.templates.waitlist_confirmation import render
    subject, html, text = render({"plan": "elite", "currency": "GBP"})
    assert "elite" in subject and "elite" in html
    assert "GBP" in html and "GBP" in text


def test_waitlist_confirmation_template_omits_currency_when_blank():
    from app.integrations.resend.templates.waitlist_confirmation import render
    _, html, _ = render({"plan": "pro"})
    assert "()" not in html


def test_deadline_reminder_template():
    from app.integrations.resend.templates.deadline_reminder import render
    subject, html, text = render({
        "name": "Alice",
        "upcoming": [
            {"title": "MS Computer Science — Manchester", "deadline_iso": "2026-06-26", "days_left": 5},
            {"title": "Chevening 2027", "deadline_iso": "2026-07-01", "days_left": 10},
        ],
        "dashboard_url": "https://aidwiseai.com/tracker",
    })
    assert "AidwiseAI" in subject
    assert "deadline" in subject.lower()
    assert "Alice" in html
    assert "MS Computer Science" in html and "Chevening 2027" in html
    assert "5 day" in html and "10 day" in html
    assert "https://aidwiseai.com/tracker" in html
    assert "MS Computer Science" in text and "Chevening 2027" in text


def test_deadline_reminder_template_handles_missing_dashboard_url():
    from app.integrations.resend.templates.deadline_reminder import render
    _, html, _ = render({
        "name": "Bob",
        "upcoming": [{"title": "X", "deadline_iso": "2026-06-26", "days_left": 3}],
    })
    assert "Open tracker" not in html


def test_priority_alert_template():
    from app.integrations.resend.templates.priority_alert import render
    subject, html, text = render({
        "name": "Alice",
        "scholarships": [
            {"title": "Chevening 2027", "deadline_iso": "2026-06-26", "country": "GB"},
            {"title": "DAAD WISE", "deadline_iso": "2026-06-29", "country": "DE"},
        ],
        "dashboard_url": "https://aidwiseai.com/feed",
    })
    assert "AidwiseAI" in subject
    assert "Chevening 2027" in html and "DAAD WISE" in html
    assert "GB" in html and "DE" in html
    assert "https://aidwiseai.com/feed" in html
    assert "Chevening 2027" in text


def test_priority_alert_template_singular_subject():
    from app.integrations.resend.templates.priority_alert import render
    subject, _, _ = render({
        "name": "Bob",
        "scholarships": [{"title": "X", "deadline_iso": "2026-06-26", "country": "GB"}],
    })
    assert "1 priority scholarship " in subject and "scholarships" not in subject


def test_send_transactional_accepts_all_templates(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    for name, ctx in [
        ("account_deletion_scheduled", {"name": "x", "scheduled_deletion_at": "2026-06-26", "cancel_url": "https://a/c"}),
        ("account_deletion_cancelled", {"name": "x"}),
        ("waitlist_confirmation", {"plan": "elite", "currency": "GBP"}),
        ("deadline_reminder", {
            "name": "x",
            "upcoming": [{"title": "Y", "deadline_iso": "2026-06-26", "days_left": 3}],
            "dashboard_url": "https://a/t",
        }),
        ("priority_alert", {
            "name": "x",
            "scholarships": [{"title": "Y", "deadline_iso": "2026-06-26", "country": "GB"}],
            "dashboard_url": "https://a/f",
        }),
    ]:
        with patch("app.integrations.resend.send.resend") as mock_resend:
            mock_resend.Emails.send.return_value = {"id": f"msg_{name}"}
            result = send_transactional(to="u@x.com", template=name, context=ctx)
            assert result == f"msg_{name}"
