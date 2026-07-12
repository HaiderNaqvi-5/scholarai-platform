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


def _canonicalize(schema: dict) -> dict:
    """Strip pydantic/fastapi version-specific serialization noise so the gate
    checks the real app contract (paths, fields, types, required) and not the
    library's rendering of it. Absorbs the deltas between the pinned CI stack
    (fastapi 0.115.0 / pydantic 2.10.6) and newer local versions:
      - framework-generated validation-error schemas (ctx/input properties
        appear only on newer pydantic),
      - integral floats (2.10 emits ``0``; 2.12 emits ``0.0``),
      - ``additionalProperties: true`` (emitted only by newer pydantic),
      - the binary-upload indicator (``format: binary`` vs ``contentMediaType``
        flips between fastapi versions).
    None of these are contract-meaningful for the hand-synced frontend types,
    so removing them keeps the gate loud on real drift and quiet on library bumps.
    """
    schema = copy.deepcopy(schema)
    comps = schema.get("components", {}).get("schemas", {})
    for name in ("ValidationError", "HTTPValidationError"):
        comps.pop(name, None)

    def walk(node):
        if isinstance(node, dict):
            node.pop("contentMediaType", None)
            if node.get("format") == "binary":
                node.pop("format", None)
            if node.get("additionalProperties") is True:
                node.pop("additionalProperties", None)
            for key in list(node.keys()):
                val = node[key]
                if isinstance(val, float) and val.is_integer():
                    node[key] = int(val)
                walk(node[key])
        elif isinstance(node, list):
            for i, item in enumerate(node):
                if isinstance(item, float) and item.is_integer():
                    node[i] = int(item)
                walk(node[i])

    walk(schema)
    return schema


def _schema_json(schema: dict) -> str:
    canon = _canonicalize(_normalize_schema(schema))
    # sort_keys + fixed indent => deterministic byte-for-byte output across runs.
    return json.dumps(canon, sort_keys=True, indent=2) + "\n"


def _current_schema_json() -> str:
    return _schema_json(create_app().openapi())


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

    # Canonicalize the on-disk snapshot the same way as the live schema so a
    # snapshot captured under a different fastapi/pydantic build still compares
    # equal. _normalize_newlines collapses any CRLF a checkout introduced
    # (Path.read_text newline= is Python 3.13+, CI runs 3.12).
    raw = _normalize_newlines(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    snapshot = _normalize_newlines(_schema_json(json.loads(raw)))
    assert current == snapshot, (
        "OpenAPI schema drifted from the checked-in snapshot "
        f"({SNAPSHOT_PATH}). This means the backend API contract changed.\n"
        "1. Review the diff and update frontend/src/lib/api/types.ts to match.\n"
        "2. Regenerate the snapshot:\n"
        f"   UPDATE_OPENAPI_SNAPSHOT=1 python -m pytest {__file__} -q\n"
        "3. Commit the updated openapi.snapshot.json alongside your API change."
    )
