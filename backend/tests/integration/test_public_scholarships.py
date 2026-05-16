from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.api.v1.routes.scholarships import get_optional_user
from app.core.database import get_db
from app.models import RecordState, Scholarship, ScholarshipTier, UserRole


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

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None


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


# ── Premium-paywall fixtures (Task 13) ────────────────────────────────────────

def _build_standard_row() -> Scholarship:
    row = Scholarship(
        title="Chevening Standard Award",
        provider_name="Chevening",
        country_code="CA",
        summary="Standard published scholarship",
        funding_summary="Tuition + stipend",
        funding_type="full_funding",
        funding_amount_min=20000,
        funding_amount_max=30000,
        source_url="https://example.org/chevening-standard",
        field_tags=["public policy"],
        degree_levels=["MS"],
        citizenship_rules=["PK"],
        record_state=RecordState.PUBLISHED,
        tier=ScholarshipTier.STANDARD,
        deadline_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
    )
    row.id = uuid4()
    return row


def _build_premium_row() -> Scholarship:
    row = Scholarship(
        title="Rhodes Premium Fellowship",
        provider_name="Rhodes Trust",
        country_code="CA",
        summary="Premium-tier marquee award",
        funding_summary="Full ride + stipend",
        funding_type="full_funding",
        funding_amount_min=50000,
        funding_amount_max=80000,
        source_url="https://example.org/rhodes-premium",
        field_tags=["interdisciplinary"],
        degree_levels=["MS"],
        citizenship_rules=["PK"],
        record_state=RecordState.PUBLISHED,
        tier=ScholarshipTier.PREMIUM,
        deadline_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )
    row.id = uuid4()
    return row


class _TierAwareSession:
    """Fake AsyncSession that honours a tier filter on the SQLAlchemy statement.

    Used to assert the list-endpoint tier predicate actually narrows the
    returned rowset — not just that the view filters them in Python.
    """

    def __init__(self, rows: list[Scholarship]) -> None:
        self._rows = rows

    async def execute(self, query):  # noqa: ANN001 — duck-typed Select
        try:
            rendered = str(
                query.compile(compile_kwargs={"literal_binds": True})
            ).lower()
        except Exception:  # noqa: BLE001 — fall back to raw repr
            rendered = str(query).lower()
        if "scholarships.tier = 'standard'" in rendered:
            filtered = [row for row in self._rows if row.tier == ScholarshipTier.STANDARD]
        else:
            filtered = list(self._rows)
        return FakeExecuteResult(filtered)


class _SingleRowSession:
    """Fake AsyncSession that always returns one scholarship row."""

    def __init__(self, row: Scholarship) -> None:
        self._row = row

    async def execute(self, _query):
        return FakeExecuteResult([self._row])


def _make_user(plan: str):
    return SimpleNamespace(
        id=uuid4(),
        role=UserRole.STUDENT,
        is_active=True,
        plan=plan,
        plan_currency="PKR",
    )


def _override_optional_user(user):
    async def _override():
        return user

    return _override


def test_anon_catalog_excludes_premium(app, client):
    standard = _build_standard_row()
    premium = _build_premium_row()
    session = _TierAwareSession([standard, premium])

    async def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_optional_user] = _override_optional_user(None)

    response = client.get("/api/v1/scholarships?page=1&page_size=12")

    assert response.status_code == 200, response.text
    titles = {item["title"] for item in response.json()["items"]}
    assert standard.title in titles
    assert premium.title not in titles


def test_free_catalog_excludes_premium(app, client):
    standard = _build_standard_row()
    premium = _build_premium_row()
    session = _TierAwareSession([standard, premium])

    async def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_optional_user] = _override_optional_user(_make_user("free"))

    response = client.get(
        "/api/v1/scholarships?page=1&page_size=12",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200, response.text
    titles = {item["title"] for item in response.json()["items"]}
    assert standard.title in titles
    assert premium.title not in titles


def test_pro_catalog_includes_premium(app, client):
    standard = _build_standard_row()
    premium = _build_premium_row()
    session = _TierAwareSession([standard, premium])

    async def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_optional_user] = _override_optional_user(_make_user("pro"))

    response = client.get(
        "/api/v1/scholarships?page=1&page_size=12",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200, response.text
    titles = {item["title"] for item in response.json()["items"]}
    assert premium.title in titles
    assert standard.title in titles


def test_premium_detail_blocked_for_free(app, client):
    premium = _build_premium_row()
    session = _SingleRowSession(premium)

    async def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_optional_user] = _override_optional_user(_make_user("free"))

    response = client.get(
        f"/api/v1/scholarships/{premium.id}",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 402, response.text
    body = response.json()
    # ErrorEnvelope middleware wraps HTTPException detail under "error.details"
    # for non-2xx routes; either shape is acceptable as long as the discriminator
    # surfaces.
    detail = body.get("detail")
    if detail is None:
        detail = body.get("error", {}).get("details")
    assert detail is not None, body
    assert detail.get("error") == "plan_required"


def test_premium_detail_allowed_for_pro(app, client):
    premium = _build_premium_row()
    session = _SingleRowSession(premium)

    async def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_optional_user] = _override_optional_user(_make_user("pro"))

    response = client.get(
        f"/api/v1/scholarships/{premium.id}",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["title"] == premium.title


def test_standard_detail_open_to_all(app, client):
    standard = _build_standard_row()
    session = _SingleRowSession(standard)

    async def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_optional_user] = _override_optional_user(None)
    anon_response = client.get(f"/api/v1/scholarships/{standard.id}")
    assert anon_response.status_code == 200, anon_response.text
    assert anon_response.json()["title"] == standard.title

    app.dependency_overrides[get_optional_user] = _override_optional_user(_make_user("free"))
    free_response = client.get(
        f"/api/v1/scholarships/{standard.id}",
        headers={"Authorization": "Bearer fake"},
    )
    assert free_response.status_code == 200, free_response.text
    assert free_response.json()["title"] == standard.title


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
