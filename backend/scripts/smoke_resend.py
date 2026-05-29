"""One-off Resend smoke test.

Sends a single "Hello World" email via Resend to verify the API key works.
Reads RESEND_API_KEY from the environment so the key is never hardcoded.

Usage:
    cd backend
    # ensure RESEND_API_KEY=re_... is set in backend/.env
    python scripts/smoke_resend.py [recipient@example.com]

Notes:
- Default `from` is Resend's sandbox sender `onboarding@resend.dev`. It only
  delivers to the email registered on your Resend account. For real sends,
  switch to a verified-domain sender (e.g. noreply@aidwiseai.com).
- SDK 2.5.x returns a dict with an `id` key; we access it via `.get("id")`
  to stay compatible with both dict and object responses.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import resend
from dotenv import load_dotenv


DEFAULT_RECIPIENT = "2k22bscs238@undergrad.nfciet.edu.pk"

# Load backend/.env so bare `python scripts/smoke_resend.py` picks up keys
# the same way the FastAPI app does via pydantic-settings.
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


def main() -> int:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("ERROR: RESEND_API_KEY not set. Add it to backend/.env or export it.", file=sys.stderr)
        return 1

    recipient = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RECIPIENT
    sender = os.environ.get("RESEND_FROM_ADDRESS", "onboarding@resend.dev")

    resend.api_key = api_key
    response = resend.Emails.send({
        "from": sender,
        "to": recipient,
        "subject": "Hello World",
        "html": "<p>Congrats on sending your <strong>first email</strong>!</p>",
    })

    message_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
    print(f"sent id={message_id} to={recipient} from={sender}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
