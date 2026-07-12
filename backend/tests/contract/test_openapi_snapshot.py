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

import copy
import json
import os
from pathlib import Path

from app.main import create_app

SNAPSHOT_PATH = Path(__file__).parent / "openapi.snapshot.json"

# info.title/info.version are read from Settings (APP_NAME/APP_VERSION),
# which pydantic BaseSettings loads from backend/.env when cwd is backend/.
# That makes them differ between "pytest from repo root" (.env not loaded,
# config.py defaults win) and "pytest from backend/" (.env loaded) even
# though the actual API contract (paths + components) hasn't changed. Pin
# them to fixed placeholders so the snapshot gate only detects real drift.
_NORMALIZED_TITLE = "<normalized-app-title>"
_NORMALIZED_VERSION = "<normalized-app-version>"


def _normalize_schema(schema: dict) -> dict:
    schema = copy.deepcopy(schema)
    info = schema.get("info", {})
    if "title" in info:
        info["title"] = _NORMALIZED_TITLE
    if "version" in info:
        info["version"] = _NORMALIZED_VERSION
    return schema


def _current_schema_json() -> str:
    app = create_app()
    schema = _normalize_schema(app.openapi())
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
        # write_bytes pins the regenerated snapshot to LF on disk regardless of
        # platform (no universal-newline translation), so it stays byte-stable
        # across OSes/checkouts. (Path.read_text/write_text gained newline= only
        # in Python 3.13; CI runs 3.12, so avoid that kwarg.)
        SNAPSHOT_PATH.write_bytes(current.encode("utf-8"))
        return

    assert SNAPSHOT_PATH.exists(), (
        f"Missing OpenAPI snapshot at {SNAPSHOT_PATH}. Generate it with:\n"
        f"  UPDATE_OPENAPI_SNAPSHOT=1 python -m pytest {__file__} -q"
    )

    # _normalize_newlines collapses any CRLF a checkout introduced, so a plain
    # read is enough (Path.read_text newline= is Python 3.13+, CI runs 3.12).
    snapshot = _normalize_newlines(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert current == snapshot, (
        "OpenAPI schema drifted from the checked-in snapshot "
        f"({SNAPSHOT_PATH}). This means the backend API contract changed.\n"
        "1. Review the diff and update frontend/src/lib/api/types.ts to match.\n"
        "2. Regenerate the snapshot:\n"
        f"   UPDATE_OPENAPI_SNAPSHOT=1 python -m pytest {__file__} -q\n"
        "3. Commit the updated openapi.snapshot.json alongside your API change."
    )
