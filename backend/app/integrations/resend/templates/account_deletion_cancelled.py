def render(ctx: dict) -> tuple[str, str, str]:
    name = ctx.get("name") or "there"
    subject = "AidwiseAI: account deletion cancelled"
    html = (
        f"<p>Hi {name},</p>"
        f"<p>Your AidwiseAI account deletion has been cancelled. "
        f"Your account remains active.</p>"
    )
    text = (
        f"Hi {name},\n\n"
        f"Your AidwiseAI account deletion has been cancelled. "
        f"Your account remains active."
    )
    return subject, html, text
