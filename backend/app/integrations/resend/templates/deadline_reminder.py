def render(ctx: dict) -> tuple[str, str, str]:
    name = ctx.get("name") or "there"
    upcoming = ctx.get("upcoming") or []
    dashboard_url = ctx.get("dashboard_url") or ""

    count = len(upcoming)
    plural = "s" if count != 1 else ""
    subject = f"AidwiseAI: {count} application deadline{plural} approaching"

    items_html = "".join(
        f"<li><strong>{i['title']}</strong> — "
        f"{i['deadline_iso']} ({i['days_left']} day"
        f"{'s' if i['days_left'] != 1 else ''} left)</li>"
        for i in upcoming
    )
    cta_html = (
        f'<p><a href="{dashboard_url}" '
        f'style="display:inline-block;padding:10px 18px;'
        f'background:#1B3A6B;color:#FBF7EE;text-decoration:none;'
        f'border-radius:8px;">Open tracker</a></p>'
        if dashboard_url
        else ""
    )
    html = (
        f"<p>Hi {name},</p>"
        f"<p>You have {count} application deadline{plural} coming up:</p>"
        f"<ul>{items_html}</ul>"
        f"{cta_html}"
        f"<p style='color:#6b7280;font-size:12px;'>"
        f"Reminders run daily. Mute or change cadence in your "
        f"AidwiseAI settings.</p>"
    )

    items_text = "\n".join(
        f"- {i['title']} — {i['deadline_iso']} ({i['days_left']} day"
        f"{'s' if i['days_left'] != 1 else ''} left)"
        for i in upcoming
    )
    cta_text = f"\n\nOpen tracker: {dashboard_url}" if dashboard_url else ""
    text = (
        f"Hi {name},\n\n"
        f"You have {count} application deadline{plural} coming up:\n\n"
        f"{items_text}"
        f"{cta_text}"
    )
    return subject, html, text
