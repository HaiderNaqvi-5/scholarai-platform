def render(ctx: dict) -> tuple[str, str, str]:
    name = ctx.get("name") or "there"
    url = ctx.get("download_url") or ""

    subject = "AidwiseAI: your data export is ready"

    cta = (
        f'<p><a href="{url}" '
        f'style="display:inline-block;padding:10px 18px;'
        f'background:#1B3A6B;color:#FBF7EE;text-decoration:none;'
        f'border-radius:8px;">Download export</a></p>'
        if url
        else ""
    )

    html = (
        f"<p>Hi {name},</p>"
        f"<p>Your AidwiseAI data export is ready.</p>"
        f"{cta}"
        f"<p style='color:#6b7280;font-size:12px;'>"
        f"This link is valid for 24 hours. The bundle contains your profile, "
        f"tracker, documents, interview transcripts, and consent history.</p>"
    )
    text = (
        f"Hi {name},\n\n"
        f"Your AidwiseAI data export is ready.\n\n"
        f"Download: {url}\n\n"
        f"This link is valid for 24 hours."
    )
    return subject, html, text
