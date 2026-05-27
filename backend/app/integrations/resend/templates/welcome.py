def render(ctx: dict) -> tuple[str, str, str]:
    name = ctx.get("name", "there")
    subject = "Welcome to GrantPath"
    html = f"<p>Hi {name}, welcome to GrantPath.</p>"
    text = f"Hi {name}, welcome to GrantPath."
    return subject, html, text
