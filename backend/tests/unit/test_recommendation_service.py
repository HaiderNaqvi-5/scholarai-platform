from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models import DegreeLevel, RecordState
from app.services.recommendations import RecommendationService

pytestmark = pytest.mark.asyncio


class ScalarResult:
    def __init__(self, all_items=None):
        self.all_items = all_items or []

    def scalars(self):
        return self

    def all(self):
        return self.all_items


class FakeSession:
    def __init__(self, results):
        self.results = list(results)

    async def execute(self, _query):
        return self.results.pop(0)


async def test_recommendation_service_builds_demo_quality_explanations():
    profile = SimpleNamespace(
        citizenship_country_code="PK",
        gpa_value=Decimal("3.70"),
        gpa_scale=Decimal("4.0"),
        target_field="Data Science",
        target_degree_level=DegreeLevel.MS,
        target_country_code="CA",
    )
    scholarship = SimpleNamespace(
        id=uuid4(),
        title="UBC MDS Excellence Entrance Award",
        provider_name="University of British Columbia",
        country_code="CA",
        deadline_at=datetime(2026, 12, 1, tzinfo=timezone.utc),
        record_state=RecordState.PUBLISHED,
        source_url="https://www.grad.ubc.ca/awards/mds-excellence-entrance-award",
        field_tags=["data science", "analytics"],
        degree_levels=["MS"],
        citizenship_rules=[],
        min_gpa_value=Decimal("3.30"),
    )
    internal_only = SimpleNamespace(
        id=uuid4(),
        title="Internal Validated Record",
        provider_name="Internal Provider",
        country_code="CA",
        deadline_at=None,
        record_state=RecordState.VALIDATED,
        source_url="https://example.com/internal",
        field_tags=["analytics"],
        degree_levels=["MS"],
        citizenship_rules=[],
        min_gpa_value=Decimal("3.00"),
    )

    service = RecommendationService(FakeSession([ScalarResult([scholarship, internal_only])]))
    items = await service.build_for_profile(profile, limit=5)

    assert len(items) == 1
    item = items[0]
    assert item.title == "UBC MDS Excellence Entrance Award"
    assert item.fit_band == "strong"
    assert item.record_state == "published"
    assert item.match_summary
    assert len(item.matched_criteria) >= 3
    assert "published minimum" in " ".join(item.matched_criteria).lower()
