"""Contract gate: fail CI when the FastAPI OpenAPI schema drifts.

Closes security-audit.md D7. Frontend types (frontend/src/lib/api/types.ts)
are hand-synced to backend Pydantic schemas with no codegen — this test does
not replace that codegen (out of scope), it just makes drift loud instead of
silent so a schema change forces a deliberate FE type review.

Regenerating the snapshot after an intentional API change:

    UPDATE_OPENAPI_SNAPSHOT=1 python -m pytest backend/tests/contract/test_openapi_snapshot.py -q

then review the diff, update frontend/src/lib/api/types.ts to match, and
commit the regenerated backend/tests/contract/openapi.snapshot.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from app.main import create_app

SNAPSHOT_PATH = Path(__file__).parent / "openapi.snapshot.json"


def _current_schema_json() -> str:
    app = create_app()
    schema = app.openapi()
    # sort_keys + fixed indent => deterministic byte-for-byte output across runs.
    return json.dumps(schema, sort_keys=True, indent=2) + "\n"


def _normalize_newlines(text: str) -> str:
    # Line-ending-agnostic: git checkout (core.autocrlf) can hand us CRLF on
    # Windows even though the schema content is unchanged. Compare on content,
    # not on-disk line endings.
    return text.replace("\r\n", "\n").replace("\r", "\n")


def test_openapi_schema_matches_snapshot():
    current = _normalize_newlines(_current_schema_json())

    if os.environ.get("UPDATE_OPENAPI_SNAPSHOT") == "1":
        # newline="\n" pins the regenerated snapshot to LF on disk regardless
        # of platform, so it stays byte-stable across OSes/checkouts.
        SNAPSHOT_PATH.write_text(current, encoding="utf-8", newline="\n")
        return

    assert SNAPSHOT_PATH.exists(), (
        f"Missing OpenAPI snapshot at {SNAPSHOT_PATH}. Generate it with:\n"
        f"  UPDATE_OPENAPI_SNAPSHOT=1 python -m pytest {__file__} -q"
    )

    # newline="" disables universal-newline translation so we normalize
    # explicitly ourselves instead of relying on implicit platform behavior.
    snapshot = _normalize_newlines(
        SNAPSHOT_PATH.read_text(encoding="utf-8", newline="")
    )
    assert current == snapshot, (
        "OpenAPI schema drifted from the checked-in snapshot "
        f"({SNAPSHOT_PATH}). This means the backend API contract changed.\n"
        "1. Review the diff and update frontend/src/lib/api/types.ts to match.\n"
        "2. Regenerate the snapshot:\n"
        f"   UPDATE_OPENAPI_SNAPSHOT=1 python -m pytest {__file__} -q\n"
        "3. Commit the updated openapi.snapshot.json alongside your API change."
    )
