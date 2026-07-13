import importlib
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4
import pytest


def test_graph_sync_module_imports_cleanly():
    mod = importlib.import_module("app.tasks.graph_sync_tasks")
    assert hasattr(mod, "sync_knowledge_graph")


async def test_gpa_passed_as_string_preserves_precision():
    from app.tasks import graph_sync_tasks as g
    recorded = {}

    class FakeTx:
        async def run(self, query, **params):
            recorded.update(params)

    profile = SimpleNamespace(
        id=uuid4(), gpa_value=Decimal("3.67"), target_degree_level=None,
        citizenship_country_code="PK", target_country_code="GB",
    )
    await g._merge_student_tx(FakeTx(), profile)
    assert recorded["gpa"] == "3.67"
    assert not isinstance(recorded["gpa"], float)


async def test_scholarship_gpa_as_string_and_lists_coerced():
    from app.tasks import graph_sync_tasks as g
    recorded = {}

    class FakeTx:
        async def run(self, query, **params):
            recorded.update(params)

    sch = SimpleNamespace(
        id=uuid4(), country_code="GB", min_gpa_value=Decimal("3.50"),
        degree_levels=["MS"], citizenship_rules=[],
    )
    await g._merge_scholarship_tx(FakeTx(), sch)
    assert recorded["gpa"] == "3.50" and not isinstance(recorded["gpa"], float)
    assert recorded["degrees"] == ["MS"] and recorded["citizenships"] == []
