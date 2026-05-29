def render(ctx: dict) -> tuple[str, str, str]:
    name = ctx.get("name") or "there"
    scheduled_at = ctx.get("scheduled_deletion_at") or ""
    cancel_url = ctx.get("cancel_url") or ""

    subject = "AidwiseAI: account deletion scheduled"

    cta = (
        f'<p><a href="{cancel_url}" '
        f'style="display:inline-block;padding:10px 18px;'
        f'background:#1B3A6B;color:#FBF7EE;text-decoration:none;'
        f'border-radius:8px;">Cancel deletion</a></p>'
        if cancel_url
        else ""
    )

    html = (
        f"<p>Hi {name},</p>"
        f"<p>Your AidwiseAI account is scheduled for deletion on "
        f"<strong>{scheduled_at}</strong> (30 days from now).</p>"
        f"<p>If you change your mind, you can cancel any time before that date.</p>"
        f"{cta}"
        f"<p style='color:#6b7280;font-size:12px;'>"
        f"Consent audit logs are retained for 7 years per legal requirement, "
        f"with PII anonymised on the deletion date.</p>"
    )
    text = (
        f"Hi {name},\n\n"
        f"Your AidwiseAI account is scheduled for deletion on {scheduled_at} "
        f"(30 days from now).\n\n"
        f"Cancel deletion: {cancel_url}\n\n"
        f"Consent audit logs are retained for 7 years."
    )
    return subject, html, text
