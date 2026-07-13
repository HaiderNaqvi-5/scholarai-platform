from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import ApplicationStatus, IngestionRunStatus, UserRole


class _DummyCurrentUser:
    def __init__(self):
        self.role = UserRole.ADMIN
        self._token_capabilities = {
            "admin.audit.read",
            "owner.system.read",
        }


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _RowsResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def one(self):
        return self._rows[0]


class _FakeAnalyticsDB:
    """Routes each query by its rendered SQL to the matching fake result.

    After perf-db-04 the route issues exactly four count-bearing queries
    (down from eleven): a users GROUP BY role, a single scholarship scalar,
    a two-column applications aggregate, a single document scalar, a single
    interview scalar, and a two-column ingestion-runs aggregate — plus the
    three unchanged KPI ``GROUP BY policy_version`` queries.
    """

    def __init__(self):
        # users GROUP BY role -> (role_value, count) rows.
        # student bucket = STUDENT(6) + ENDUSER_STUDENT(1) = 7
        # mentor bucket  = MENTOR(2) + INTERNAL_USER(1)   = 3
        # admin bucket   = ADMIN(2) + DEV(1) + OWNER(1)   = 4
        # plus UNIVERSITY(1), counted in total only       -> total = 15
        self.user_role_rows = [
            (UserRole.STUDENT.value, 6),
            (UserRole.ENDUSER_STUDENT.value, 1),
            (UserRole.MENTOR.value, 2),
            (UserRole.INTERNAL_USER.value, 1),
            (UserRole.ADMIN.value, 2),
            (UserRole.DEV.value, 1),
            (UserRole.OWNER.value, 1),
            (UserRole.UNIVERSITY.value, 1),
        ]
        # applications aggregate -> (total, submitted)
        self.application_row = (11, 5)
        # ingestion runs aggregate -> (total, failed)
        self.ingestion_row = (4, 1)
        self.scholarship_count = 20
        self.document_count = 8
        self.interview_count = 7
        # three KPI trend GROUP BY policy_version queries (unchanged shape)
        self.kpi_rows = [
            [("reco.kpi.v1", 6, 4)],
            [("document.quality.v1", 5, 3)],
            [("interview.progression.v1", 4, 2)],
        ]
        self._kpi_idx = 0

    async def execute(self, query):
        text = str(query)
        if "GROUP BY users.role" in text or "GROUP BY anon_1.role" in text:
            return _RowsResult(self.user_role_rows)
        if "GROUP BY" in text:
            rows = self.kpi_rows[self._kpi_idx]
            self._kpi_idx += 1
            return _RowsResult(rows)
        if "FROM applications" in text:
            return _RowsResult([self.application_row])
        if "FROM ingestion_runs" in text:
            return _RowsResult([self.ingestion_row])
        if "FROM scholarships" in text:
            return _ScalarResult(self.scholarship_count)
        if "FROM documents" in text:
            return _ScalarResult(self.document_count)
        if "FROM interview_sessions" in text:
            return _ScalarResult(self.interview_count)
        raise AssertionError(f"unexpected analytics query: {text}")


def test_analytics_includes_kpi_trends(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _FakeAnalyticsDB()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.get(
        "/api/v1/analytics",
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert "kpi_trends" in payload
    assert len(payload["kpi_trends"]) == 3
    assert payload["kpi_trends"][0]["metric_domain"] == "recommendation"


def test_analytics_buckets_role_counts_from_single_group_by(app, client):
    async def override_current_user():
        return _DummyCurrentUser()

    async def override_db():
        yield _FakeAnalyticsDB()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.get(
        "/api/v1/analytics",
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    # total counts every role (incl. UNIVERSITY), buckets follow the
    # STUDENT+ENDUSER_STUDENT / MENTOR+INTERNAL_USER / ADMIN+DEV+OWNER split.
    # 6+1 + 2+1 + 2+1+1 + 1(UNIVERSITY) = 15 across all eight role rows.
    assert payload["total_users"] == 15
    assert payload["student_count"] == 7
    assert payload["mentor_count"] == 3
    assert payload["admin_count"] == 4
    # two-column aggregates unpack correctly
    assert payload["total_applications"] == 11
    assert payload["submitted_applications"] == 5
    assert payload["ingestion_runs_total"] == 4
    assert payload["ingestion_runs_failed"] == 1
    # untouched scalar counts
    assert payload["total_scholarships"] == 20
    assert payload["total_documents"] == 8
    assert payload["total_interview_sessions"] == 7
