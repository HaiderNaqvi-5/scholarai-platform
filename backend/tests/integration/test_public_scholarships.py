from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.api.v1.routes.scholarships import get_optional_user
from app.core.database import get_db
from app.models import RecordState, Scholarship, ScholarshipTier, UserRole
from tests.conftest import requires_db


def _published(
    title,
    *,
    country="CA",
    funding_type="stipend",
    amount_min=10000,
    amount_max=20000,
    deadline=None,
    field_tags=None,
    tier=ScholarshipTier.STANDARD,
    provider="Prov",
):
    return Scholarship(
        title=title,
        provider_name=provider,
        country_code=country,
        summary=f"{title} summary",
        funding_summary="funding",
        funding_type=funding_type,
        funding_amount_min=amount_min,
        funding_amount_max=amount_max,
        source_url=f"https://example.org/{title.replace(' ', '-').lower()}",
        field_tags=field_tags or ["data science"],
        degree_levels=["MS"],
        citizenship_rules=["PK"],
        record_state=RecordState.PUBLISHED,
        tier=tier,
        deadline_at=deadline or datetime(2026, 9, 1, tzinfo=timezone.utc),
    )


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

    def scalar_one(self):
        return len(self._items)

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None


def _stmt_is_count(query) -> bool:
    """True when the statement is the ``select(func.count())`` total query."""
    try:
        from sqlalchemy.sql import functions

        return any(
            isinstance(col, functions.count) for col in query.selected_columns
        )
    except Exception:  # noqa: BLE001 — non-Select / introspection miss
        return False


def _render(query) -> str:
    try:
        return str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    except Exception:  # noqa: BLE001 — fall back to raw repr
        return str(query).lower()


class _CatalogFakeDB:
    """Fake AsyncSession that faithfully evaluates the catalog query against an
    in-memory rowset.

    The list handler now issues two statements per request: a ``count(*)`` total
    and a paged ``SELECT`` with WHERE + ORDER BY + OFFSET/LIMIT. This fake reads
    the same query params off the rendered SQL and applies the equivalent Python
    filters/sort/slice so the existing behavioral assertions (filtered totals,
    page sizing) still hold without a live database. It is NOT a generic SQL
    engine — it only understands the predicates ``list_scholarships`` emits.
    """

    def __init__(self, rows):
        self._rows = list(rows)

    # — predicate evaluation mirroring the SQL WHERE clause ——————————————
    def _matching(self, sql: str) -> list[Scholarship]:
        rows = self._rows
        # record_state is always PUBLISHED in this surface; the fixtures only
        # hold published rows, so no extra filtering is needed for it.
        if "scholarships.tier = 'standard'" in sql:
            # Unsaved ORM rows that omit ``tier`` read as ``None`` in memory; the
            # column's server/Python default is STANDARD, so treat None as such.
            rows = [
                r
                for r in rows
                if (r.tier or ScholarshipTier.STANDARD) == ScholarshipTier.STANDARD
            ]
        country = _between(sql, "scholarships.country_code = '", "'")
        if country:
            rows = [r for r in rows if (r.country_code or "").lower() == country]
        funding = _between(sql, "lower(scholarships.funding_type) = '", "'")
        if funding:
            rows = [r for r in rows if (r.funding_type or "").lower() == funding]
        provider = _ilike_term(sql, "scholarships.provider_name")
        if provider:
            rows = [r for r in rows if provider in (r.provider_name or "").lower()]
        tag = _ilike_term(sql, "cast(scholarships.field_tags as text)")
        if tag:
            rows = [
                r
                for r in rows
                if tag in " ".join(t.lower() for t in (r.field_tags or []))
            ]
        return rows

    async def execute(self, query):  # noqa: ANN001 — duck-typed Select
        sql = _render(query)
        rows = self._matching(sql)
        if _stmt_is_count(query):
            return FakeExecuteResult(rows)
        offset = getattr(query, "_offset", None) or 0
        limit = getattr(query, "_limit", None)
        page = rows[offset : (offset + limit) if limit is not None else None]
        return FakeExecuteResult(page)


def _between(text: str, prefix: str, suffix: str) -> str | None:
    start = text.find(prefix)
    if start == -1:
        return None
    start += len(prefix)
    end = text.find(suffix, start)
    return text[start:end] if end != -1 else None


def _ilike_term(text: str, column: str) -> str | None:
    """Extract the lowercased ILIKE search term applied to ``column``.

    Handles both the default-dialect rendering (``lower(col) like lower('%x%')``)
    and native ``col ilike '%x%'``.
    """
    for pattern in (f"lower({column}) like lower('%", f"{column} ilike '%"):
        start = text.find(pattern)
        if start == -1:
            continue
        start += len(pattern)
        end = text.find("%'", start)
        if end != -1:
            return text[start:end]
    return None


class FakeSession(_CatalogFakeDB):
    def __init__(self):
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
        super().__init__([waterloo, ubc])


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


class _TierAwareSession(_CatalogFakeDB):
    """Fake AsyncSession that honours the tier filter on the SQLAlchemy statement.

    Used to assert the list-endpoint tier predicate actually narrows the
    returned rowset — not just that the view filters them in Python. Inherits
    the shared catalog evaluator so the SQL-pushed ``count(*)`` + paged query
    both resolve against the in-memory rows.
    """


class _SingleRowSession:
    """Fake AsyncSession for the detail endpoint — always one scholarship row."""

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


# ── perf-db-01: SQL push-down contract (offline, non-skipped) ─────────────────


class _RecordingResult:
    """Result stand-in that serves both ``.scalars().all()`` and ``.scalar_one()``.

    The count query consumes ``scalar_one`` (row total); the page query consumes
    ``scalars().all()`` (the ORM rows). One class covers both call shapes so the
    fake does not need to inspect the statement to decide what to return.
    """

    def __init__(self, items):
        self._items = items

    def scalars(self):
        return FakeScalarCollection(self._items)

    def scalar_one(self):
        return len(self._items)

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None


class _RecordingSession:
    """Fake AsyncSession that records every compiled statement it executes.

    Used to assert the list handler pushes filters/sort/pagination into SQL:
    a separate ``count(*)`` query plus a page query carrying WHERE + ORDER BY +
    LIMIT/OFFSET — rather than a single ``SELECT scholarships.*`` whole-table
    load that is filtered/sliced in Python.
    """

    def __init__(self, rows):
        self._rows = rows
        self.rendered_statements: list[str] = []

    async def execute(self, query):  # noqa: ANN001 — duck-typed Select
        try:
            rendered = str(
                query.compile(compile_kwargs={"literal_binds": True})
            ).lower()
        except Exception:  # noqa: BLE001 — fall back to raw repr
            rendered = str(query).lower()
        self.rendered_statements.append(rendered)
        if "count(" in rendered:
            return _RecordingResult(self._rows)
        return _RecordingResult(self._rows)


def test_list_handler_pushes_filters_and_pagination_into_sql(app, client):
    """The handler must build WHERE + ORDER BY + LIMIT/OFFSET in SQL and issue a
    separate count(*) — not load the whole published table and slice in Python."""
    rows = [_build_standard_row(), _build_standard_row()]
    session = _RecordingSession(rows)

    async def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_optional_user] = _override_optional_user(None)

    response = client.get(
        "/api/v1/scholarships"
        "?country_code=CA&funding_type=full_funding&provider=Chevening"
        "&field_tag=public%20policy&min_amount=5000&sort=deadline"
        "&page=2&page_size=5"
    )

    assert response.status_code == 200, response.text

    # A dedicated count(*) query was issued (separate from the page query).
    count_stmts = [s for s in session.rendered_statements if "count(" in s]
    assert count_stmts, session.rendered_statements

    # The page query carries SQL pagination (LIMIT/OFFSET) and ORDER BY — proof
    # the rows are narrowed/sliced in the database, not in Python.
    page_stmts = [s for s in session.rendered_statements if " limit " in f" {s} "]
    assert page_stmts, session.rendered_statements
    page_sql = page_stmts[0]
    assert "offset" in page_sql
    assert "order by" in page_sql
    # page=2, page_size=5 -> OFFSET 5 LIMIT 5
    assert "limit 5" in page_sql
    assert "offset 5" in page_sql

    # The query filters were pushed into the WHERE clause (not run in Python).
    # Substring checks are dialect-agnostic: the default compiler renders ILIKE
    # as ``lower(col) like lower(...)`` while the PG dialect emits native ILIKE.
    where_sql = " ".join(session.rendered_statements)
    assert "scholarships.record_state" in where_sql
    assert "scholarships.tier = 'standard'" in where_sql  # anon -> standard only
    assert "scholarships.country_code = 'ca'" in where_sql
    assert "lower(scholarships.funding_type) = 'full_funding'" in where_sql
    assert "scholarships.provider_name" in where_sql
    assert "'%chevening%'" in where_sql  # provider ILIKE pushed into SQL
    assert "cast(scholarships.field_tags as text)" in where_sql  # JSON tag match
    assert "'%public policy%'" in where_sql


@requires_db
async def test_catalog_paginates_in_sql(db_session, app_client):
    from datetime import datetime, timezone

    rows = [
        _published(f"Award {i}", deadline=datetime(2026, 9, i + 1, tzinfo=timezone.utc))
        for i in range(5)
    ]
    db_session.add_all(rows)
    await db_session.commit()

    resp = await app_client.get("/api/v1/scholarships?page=1&page_size=2&sort=deadline")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 5
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["has_more"] is True
    assert len(body["items"]) == 2
    # ORDER BY deadline_at ASC, applied in SQL -> earliest two deadlines first.
    assert body["items"][0]["title"] == "Award 0"
    assert body["items"][1]["title"] == "Award 1"

    resp_p3 = await app_client.get("/api/v1/scholarships?page=3&page_size=2&sort=deadline")
    body_p3 = resp_p3.json()
    assert body_p3["total"] == 5
    assert body_p3["has_more"] is False
    assert len(body_p3["items"]) == 1
    assert body_p3["items"][0]["title"] == "Award 4"


@requires_db
async def test_catalog_filters_in_sql(db_session, app_client):
    from datetime import datetime, timezone

    keep = _published(
        "Keep Me",
        country="CA",
        funding_type="stipend",
        amount_min=12000,
        amount_max=18000,
        field_tags=["artificial intelligence"],
        provider="Waterloo",
    )
    wrong_country = _published("Wrong Country", country="GB")
    wrong_funding = _published("Wrong Funding", funding_type="loan")
    too_small = _published("Too Small", amount_min=10, amount_max=100)
    db_session.add_all([keep, wrong_country, wrong_funding, too_small])
    await db_session.commit()

    resp = await app_client.get(
        "/api/v1/scholarships"
        "?country_code=CA&funding_type=stipend&field_tag=artificial%20intelligence"
        "&provider=Waterloo&min_amount=5000&page=1&page_size=12"
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    titles = {item["title"] for item in body["items"]}
    assert titles == {"Keep Me"}
    assert body["total"] == 1


@requires_db
async def test_catalog_excludes_premium_for_anon_in_sql(db_session, app_client):
    db_session.add_all(
        [
            _published("Std Award", tier=ScholarshipTier.STANDARD),
            _published("Premium Award", tier=ScholarshipTier.PREMIUM),
        ]
    )
    await db_session.commit()

    resp = await app_client.get("/api/v1/scholarships?page=1&page_size=12")
    assert resp.status_code == 200, resp.text
    titles = {item["title"] for item in resp.json()["items"]}
    assert "Std Award" in titles
    assert "Premium Award" not in titles
