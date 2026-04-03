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
        waterloo = Scholarship(
            title="Waterloo AI Graduate Scholarship",
            provider_name="University of Waterloo",
            country_code="CA",
            summary="Published scholarship summary",
            funding_summary="Stipend support",
            funding_type="stipend",
            funding_amount_min=12000,
            funding_amount_max=18000,
            source_url="https://uwaterloo.ca/funding/ai-scholarship",
            field_tags=["artificial intelligence", "data science"],
            degree_levels=["MS"],
            citizenship_rules=["PK"],
            record_state=RecordState.PUBLISHED,
            deadline_at=datetime(2026, 8, 15, tzinfo=timezone.utc),
        )
        waterloo.id = uuid4()

        ubc = Scholarship(
            title="UBC MDS Excellence Entrance Award",
            provider_name="University of British Columbia",
            country_code="CA",
            summary="Entrance funding for MDS applicants",
            funding_summary="Tuition support",
            funding_type="tuition_award",
            funding_amount_min=8000,
            funding_amount_max=12000,
            source_url="https://www.grad.ubc.ca/awards/mds-excellence-entrance-award",
            field_tags=["data science", "analytics"],
            degree_levels=["MS"],
            citizenship_rules=[],
            record_state=RecordState.PUBLISHED,
            deadline_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
        ubc.id = uuid4()
        return FakeExecuteResult([waterloo, ubc])


async def override_get_db():
    yield FakeSession()


def test_public_scholarships_use_paginated_envelope(app, client):
    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/api/v1/scholarships?page=1&page_size=1")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert body["has_more"] is True
    assert body["applied_filters"]["degree_level"] is None
    assert body["applied_filters"]["sort"] == "deadline"
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "Waterloo AI Graduate Scholarship"


def test_public_scholarships_apply_provider_and_funding_filters(app, client):
    app.dependency_overrides[get_db] = override_get_db

    response = client.get(
        "/api/v1/scholarships?provider=Waterloo&funding_type=stipend&field_tag=artificial%20intelligence&page=1&page_size=12"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["applied_filters"]["provider"] == "Waterloo"
    assert body["applied_filters"]["funding_type"] == "stipend"
    assert body["applied_filters"]["field_tag"] == "artificial intelligence"
    assert body["items"][0]["title"] == "Waterloo AI Graduate Scholarship"


def test_public_scholarships_invalid_sort_uses_error_envelope(client):
    response = client.get("/api/v1/scholarships?sort=unknown")

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "BAD_REQUEST"
    assert body["error"]["status"] == 400
    assert "request_id" in body["error"]
    assert body["error"]["details"]["field"] == "sort"
    assert body["error"]["details"]["received"] == "unknown"
    assert "deadline" in body["error"]["details"]["allowed_values"]


def test_public_scholarships_amount_window_conflict_uses_structured_error_details(client):
    response = client.get("/api/v1/scholarships?min_amount=5000&max_amount=100")

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "BAD_REQUEST"
    assert body["error"]["details"]["field"] == "min_amount"
    assert body["error"]["details"]["min_amount"] == 5000
    assert body["error"]["details"]["max_amount"] == 100


def test_public_scholarships_validation_error_includes_details(client):
    response = client.get("/api/v1/scholarships?query=a")

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert body["error"]["status"] == 422
    assert isinstance(body["error"]["details"]["field"], list)
    assert body["error"]["details"]["field"][0] == "query"
    assert body["error"]["details"]["errors"]
