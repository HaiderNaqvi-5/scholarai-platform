import os

import resend

from app.core.config import settings


def configure() -> None:
    # Prefer live env var so tests using monkeypatch.setenv work without
    # re-instantiating the Settings singleton. Fall back to baked Settings value.
    api_key = os.environ.get("RESEND_API_KEY") or settings.RESEND_API_KEY
    if not api_key:
        raise RuntimeError("RESEND_API_KEY not configured")
    resend.api_key = api_key
