def render(ctx: dict) -> tuple[str, str, str]:
    name = ctx.get("name", "there")
    url = ctx["download_url"]
    subject = "Your GrantPath data export is ready"
    html = f'<p>Hi {name}, your export is ready: <a href="{url}">download</a> (24h expiry).</p>'
    text = f"Hi {name}, your export is ready: {url} (24h expiry)."
    return subject, html, text
