def render(ctx: dict) -> tuple[str, str, str]:
    name = ctx.get("name") or "there"
    login_url = ctx.get("login_url") or ""

    subject = "Welcome to AidwiseAI"

    cta_html = (
        f'<p><a href="{login_url}" '
        f'style="display:inline-block;padding:10px 18px;'
        f'background:#1B3A6B;color:#FBF7EE;text-decoration:none;'
        f'border-radius:8px;">Open AidwiseAI</a></p>'
        if login_url
        else ""
    )

    html = (
        f"<p>Hi {name},</p>"
        f"<p>Welcome to <strong>AidwiseAI</strong>. Your account is ready.</p>"
        f"<p>Next steps:</p>"
        f"<ul>"
        f"<li>Complete your profile so we can match scholarships.</li>"
        f"<li>Review the eligibility checklist for your target country.</li>"
        f"<li>Save scholarships to your tracker and watch deadlines.</li>"
        f"</ul>"
        f"{cta_html}"
        f"<p style='color:#6b7280;font-size:12px;'>"
        f"You're receiving this because you signed up at AidwiseAI.</p>"
    )

    cta_text = f"\n\nOpen AidwiseAI: {login_url}" if login_url else ""
    text = (
        f"Hi {name},\n\n"
        f"Welcome to AidwiseAI. Your account is ready.\n\n"
        f"Next steps:\n"
        f"- Complete your profile so we can match scholarships.\n"
        f"- Review the eligibility checklist for your target country.\n"
        f"- Save scholarships to your tracker and watch deadlines."
        f"{cta_text}"
    )

    return subject, html, text
