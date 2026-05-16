"""PRD §0.6 critical rule: matching engine must never import B2B tables.

The recommendation/matching path must be physically incapable of being
influenced by institution licensing or referral relationships. We assert
this by source-scanning every module under app/services/recommendations
and app/services/scholarships so the property is auditable in CI.
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path

import pytest

import app.services.recommendations as rec_pkg
import app.services.reports as reports_pkg
import app.services.scholarships as scholarship_pkg


_FORBIDDEN_MODELS = {
    "Institution",
    "InstitutionStudent",
    "ReferralEnrollment",
    "UniversityLead",
}

_FORBIDDEN_TABLE_NAMES = {
    "institutions",
    "institution_students",
    "referral_enrollments",
    "university_leads",
}


def _iter_package_modules(pkg) -> list[str]:
    pkg_path = Path(pkg.__file__).parent
    return [
        name
        for _, name, _ in pkgutil.walk_packages([str(pkg_path)], prefix=pkg.__name__ + ".")
    ]


def _source_for(module_name: str) -> str:
    module = importlib.import_module(module_name)
    src_path = Path(module.__file__)
    return src_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "package",
    [rec_pkg, scholarship_pkg, reports_pkg],
    ids=["recommendations", "scholarships", "reports"],
)
def test_matching_pipeline_does_not_import_b2b_models(package) -> None:
    """Static check: forbidden ORM model names never appear in matching code."""
    offenders: dict[str, set[str]] = {}
    for module_name in _iter_package_modules(package):
        src = _source_for(module_name)
        tree = ast.parse(src, filename=module_name)
        names_used: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    names_used.add(alias.name)
            elif isinstance(node, ast.Name):
                names_used.add(node.id)
            elif isinstance(node, ast.Attribute):
                names_used.add(node.attr)
        leak = names_used & _FORBIDDEN_MODELS
        if leak:
            offenders[module_name] = leak
    assert not offenders, (
        "Matching pipeline references B2B models — PRD §0.6 trust boundary violated: "
        f"{offenders}"
    )


@pytest.mark.parametrize(
    "package",
    [rec_pkg, scholarship_pkg, reports_pkg],
    ids=["recommendations", "scholarships", "reports"],
)
def test_matching_pipeline_does_not_reference_b2b_tables(package) -> None:
    """Static check: forbidden table names never appear as raw strings either."""
    offenders: dict[str, set[str]] = {}
    for module_name in _iter_package_modules(package):
        src = _source_for(module_name).lower()
        leak = {tbl for tbl in _FORBIDDEN_TABLE_NAMES if tbl in src}
        if leak:
            offenders[module_name] = leak
    assert not offenders, (
        "Matching pipeline mentions B2B tables in source — PRD §0.6 trust boundary "
        f"violated: {offenders}"
    )
