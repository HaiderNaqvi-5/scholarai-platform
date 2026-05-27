def render(ctx: dict) -> tuple[str, str, str]:
    name = ctx.get("name") or "there"
    scholarships = ctx.get("scholarships") or []
    dashboard_url = ctx.get("dashboard_url") or ""

    count = len(scholarships)
    plural = "s" if count != 1 else ""
    subject = f"AidwiseAI: {count} priority scholarship{plural} closing soon"

    items_html = "".join(
        f"<li><strong>{s['title']}</strong> "
        f"({s['country']}) — closes {s['deadline_iso']}</li>"
        for s in scholarships
    )
    cta_html = (
        f'<p><a href="{dashboard_url}" '
        f'style="display:inline-block;padding:10px 18px;'
        f'background:#1B3A6B;color:#FBF7EE;text-decoration:none;'
        f'border-radius:8px;">Review matches</a></p>'
        if dashboard_url
        else ""
    )
    html = (
        f"<p>Hi {name},</p>"
        f"<p>{count} scholarship{plural} you qualify for "
        f"close within the next week:</p>"
        f"<ul>{items_html}</ul>"
        f"{cta_html}"
        f"<p style='color:#6b7280;font-size:12px;'>"
        f"Priority alerts are an Elite feature. Free + Pro plans see them "
        f"only at log-in.</p>"
    )

    items_text = "\n".join(
        f"- {s['title']} ({s['country']}) — closes {s['deadline_iso']}"
        for s in scholarships
    )
    cta_text = f"\n\nReview matches: {dashboard_url}" if dashboard_url else ""
    text = (
        f"Hi {name},\n\n"
        f"{count} scholarship{plural} you qualify for close within "
        f"the next week:\n\n"
        f"{items_text}"
        f"{cta_text}"
    )
    return subject, html, text
