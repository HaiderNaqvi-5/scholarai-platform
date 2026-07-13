"""Regression guard for Task 37 (P3): privacy route must not drift from
ALLOWED_CONSENT_TYPES with an inline literal.

Fully offline: inspects source via `inspect.getsource`, no DB / network.
"""

from __future__ import annotations

import ast
import inspect

from app.api.v1.routes import privacy as privacy_route
from app.core.consent import ALLOWED_CONSENT_TYPES


def test_grant_consent_uses_allowed_consent_types_constant_not_inline_set() -> None:
    """The route must reference the ALLOWED_CONSENT_TYPES constant directly
    (no re-declared inline set/list literal of consent-type strings) so the
    two can never drift apart again."""
    source = inspect.getsource(privacy_route.grant_consent)
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Set, ast.List)) and all(
            isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            for elt in node.elts
        ) and node.elts:
            raise AssertionError(
                "grant_consent() must not contain an inline string "
                "set/list literal — use ALLOWED_CONSENT_TYPES instead. "
                f"Found: {[elt.value for elt in node.elts]}"
            )

    assert "ALLOWED_CONSENT_TYPES" in source


def test_module_imports_allowed_consent_types_from_core_consent() -> None:
    assert privacy_route.ALLOWED_CONSENT_TYPES is ALLOWED_CONSENT_TYPES
