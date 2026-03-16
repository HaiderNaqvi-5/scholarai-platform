from datetime import datetime, timezone
from uuid import uuid4

from app.core.database import get_db
from app.models import RecordState, Scholarship


class FakeScalarCollection:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class FakeExecuteResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return FakeScalarCollection(self._items)


class FakeSession:
    async def execute(self, _query):
        scholarship = Scholarship(
            title="Waterloo AI Graduate Scholarship",
            provider_name="University of Waterloo",
            country_code="CA",
            summary="Published scholarship summary",
            funding_summary="Tuition support",
            source_url="https://uwaterloo.ca/funding/ai-scholarship",
            field_tags=["artificial intelligence", "data science"],
            degree_levels=["MS"],
            citizenship_rules=["PK"],
            record_state=RecordState.PUBLISHED,
            deadline_at=datetime(2026, 8, 15, tzinfo=timezone.utc),
        )
        scholarship.id = uuid4()
        return FakeExecuteResult([scholarship])


async def override_get_db():
    yield FakeSession()


def test_public_scholarships_use_list_envelope(app, client):
    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/api/v1/scholarships")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["applied_country_code"] is None
    assert body["applied_query"] is None
    assert body["applied_field_tag"] is None
    assert body["applied_degree_level"] is None
    assert body["applied_deadline_within_days"] is None
    assert body["applied_sort"] == "deadline"
    assert body["items"][0]["title"] == "Waterloo AI Graduate Scholarship"
    assert body["items"][0]["record_state"] == "published"
