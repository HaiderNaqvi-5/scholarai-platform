def render(ctx: dict) -> tuple[str, str, str]:
    plan = ctx.get("plan") or "the next tier"
    currency = ctx.get("currency") or ""

    subject = f"AidwiseAI: you're on the {plan} waitlist"

    currency_suffix = f" ({currency})" if currency else ""

    html = (
        f"<p>Thanks — you're on the waitlist for the <strong>{plan}</strong> "
        f"tier{currency_suffix}.</p>"
        f"<p>We'll email you the moment that tier opens up in your region.</p>"
        f"<p style='color:#6b7280;font-size:12px;'>"
        f"You won't be charged anything until you actively upgrade.</p>"
    )
    text = (
        f"Thanks — you're on the waitlist for the {plan} tier{currency_suffix}.\n\n"
        f"We'll email you the moment that tier opens up in your region."
    )
    return subject, html, text
