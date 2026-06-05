from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import (
    DocumentFeedback,
    DocumentInputMethod,
    DocumentProcessingStatus,
    DocumentRecord,
    DocumentType,
    UserRole,
)


class _ScalarCollection:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _ExecuteResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return _ScalarCollection(self._items)

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None


class _FakeDB:
    def __init__(self, documents: list[DocumentRecord]):
        self.documents = documents
        self.added: list[object] = []
        self.committed = False

    async def execute(self, query):
        query_text = str(query)
        if "FROM documents" in query_text and "WHERE documents.id" in query_text:
            return _ExecuteResult(self.documents[:1])
        if "FROM documents" in query_text:
            return _ExecuteResult(self.documents)
        raise AssertionError("Unexpected query executed in mentor integration test")

    def add(self, value):
        if getattr(value, "id", None) is None:
            value.id = uuid4()
        if getattr(value, "created_at", None) is None:
            value.created_at = datetime.now(timezone.utc)
        self.added.append(value)

    async def flush(self):
        return None

    async def commit(self):
        self.committed = True
        return None

    async def refresh(self, _value):
        return None


def _fake_user(capabilities: set[str], role: UserRole = UserRole.MENTOR):
    return SimpleNamespace(
        id=uuid4(),
        role=role,
        is_active=True,
        _token_capabilities=capabilities,
    )


def _build_document(*, title: str, has_human_review: bool) -> DocumentRecord:
    now = datetime.now(timezone.utc)
    document = DocumentRecord(
        user_id=uuid4(),
        title=title,
        document_type=DocumentType.SOP,
        input_method=DocumentInputMethod.TEXT,
        content_text=(
            "This draft contains enough detail to be reviewed by a mentor and includes "
            "measurable examples and clear objectives."
        ),
        processing_status=DocumentProcessingStatus.COMPLETED,
    )
    document.id = uuid4()
    document.created_at = now
    document.updated_at = now
    document.latest_feedback_at = now

    limitation_notice = (
        "Reviewed by a human mentor."
        if has_human_review
        else "This is generated guidance and should be validated separately."
    )
    feedback = DocumentFeedback(
        document_id=document.id,
        status=DocumentProcessingStatus.COMPLETED,
        feedback_payload={
            "summary": "Review summary",
            "strengths": ["Structured response"],
            "revision_priorities": ["Add one concrete result metric"],
            "caution_notes": [],
            "citations": [],
            "grounded_context_sections": {
                "validated_facts": [],
                "retrieved_writing_guidance": [],
                "generated_guidance": [],
                "limitations": [limitation_notice],
            },
        },
        limitation_notice=limitation_notice,
        completed_at=now,
    )
    feedback.id = uuid4()
    feedback.created_at = now
    document.feedback_entries = [feedback]
    return document


def test_mentor_pending_reviews_requires_authentication(client):
    response = client.get("/api/v1/mentor/pending-reviews")

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_mentor_pending_reviews_returns_only_unreviewed_documents(app, client):
    pending = _build_document(title="Pending mentor review", has_human_review=False)
    reviewed = _build_document(title="Already reviewed", has_human_review=True)
    db = _FakeDB([pending, reviewed])

    async def override_current_user():
        return _fake_user({"document.mentor.review"})

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.get(
        "/api/v1/mentor/pending-reviews?limit=10",
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == str(pending.id)
    assert payload["items"][0]["title"] == "Pending mentor review"


def test_mentor_submit_feedback_persists_human_review(app, client):
    pending = _build_document(title="Needs mentor edits", has_human_review=False)
    db = _FakeDB([pending])

    async def override_current_user():
        return _fake_user({"document.mentor.submit"})

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    response = client.post(
        f"/api/v1/mentor/documents/{pending.id}/feedback",
        json={
            "summary": "Strong structure overall with clear motivation and relevant examples.",
            "strengths": ["Clear opening", "Good fit narrative"],
            "revision_priorities": ["Quantify one project outcome"],
            "caution_notes": ["Avoid generic impact wording"],
        },
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["document_id"] == str(pending.id)
    assert payload["summary"].startswith("Strong structure")
    assert db.committed is True

    persisted_feedback = next(item for item in db.added if isinstance(item, DocumentFeedback))
    assert persisted_feedback.limitation_notice == "Reviewed by a human mentor."
    limitations = persisted_feedback.feedback_payload["grounded_context_sections"]["limitations"]
    assert limitations == ["Reviewed by a human mentor."]


# --- H5-MENTOR-IDOR: object-level ownership on mentor document read + feedback ---


def _build_owned_document(*, title: str, owner_institution_id):
    document = _build_document(title=title, has_human_review=False)
    document.owner_institution_id = owner_institution_id  # consumed by _ScopedFakeDB
    return document


class _ScopedFakeDB(_FakeDB):
    """Mirror the post-fix query: a single-document lookup only matches when the
    mentor's institution scope (passed in) equals the document owner's institution,
    OR the mentor scope is None (platform reviewer => unrestricted)."""

    def __init__(self, documents, mentor_institution_id):
        super().__init__(documents)
        self.mentor_institution_id = mentor_institution_id

    async def execute(self, query):
        query_text = str(query)
        # Only institution-scoped lookups (the post-fix query) get filtered here.
        # Detect the scope clause the fix adds: a user_id IN (SELECT users.id ...
        # WHERE users.institution_id ...) subquery. An unscoped id-only lookup
        # (the pre-fix query) falls through to the parent _FakeDB, which returns
        # the document unconditionally -> the IDOR tests then fail (200 != 404),
        # giving us a genuine red->green guard.
        is_scoped_lookup = (
            "WHERE documents.id" in query_text
            and "users.institution_id" in query_text
            and "documents.user_id IN" in query_text
        )
        if is_scoped_lookup:
            doc = self.documents[0] if self.documents else None
            if doc is None:
                return _ExecuteResult([])
            owner_inst = getattr(doc, "owner_institution_id", None)
            # mentor_institution_id is None never reaches here: the fix omits the
            # scope clause for platform reviewers, so the query is id-only and
            # falls through to super().execute (unrestricted) below.
            if owner_inst == self.mentor_institution_id:
                return _ExecuteResult([doc])
            return _ExecuteResult([])  # out-of-institution => not found
        return await super().execute(query)


def test_mentor_cannot_read_document_outside_their_institution(app, client):
    mentor_inst = uuid4()
    document = _build_owned_document(title="Other institution SOP", owner_institution_id=uuid4())
    db = _ScopedFakeDB([document], mentor_institution_id=mentor_inst)

    async def override_current_user():
        user = _fake_user({"document.mentor.review"})
        user.institution_id = mentor_inst
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    response = client.get(
        f"/api/v1/mentor/documents/{document.id}",
        headers={"Authorization": "Bearer fake"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_mentor_can_read_document_within_their_institution(app, client):
    shared_inst = uuid4()
    document = _build_owned_document(title="In institution SOP", owner_institution_id=shared_inst)
    db = _ScopedFakeDB([document], mentor_institution_id=shared_inst)

    async def override_current_user():
        user = _fake_user({"document.mentor.review"})
        user.institution_id = shared_inst
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    response = client.get(
        f"/api/v1/mentor/documents/{document.id}",
        headers={"Authorization": "Bearer fake"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(document.id)


def test_platform_admin_without_institution_reads_any_document(app, client):
    # Platform-review role (ADMIN) => unrestricted even with a null institution.
    document = _build_owned_document(title="Any student SOP", owner_institution_id=uuid4())
    db = _ScopedFakeDB([document], mentor_institution_id=None)

    async def override_current_user():
        user = _fake_user({"document.mentor.review"}, role=UserRole.ADMIN)
        user.institution_id = None  # platform reviewer (admin/owner/dev/internal)
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    response = client.get(
        f"/api/v1/mentor/documents/{document.id}",
        headers={"Authorization": "Bearer fake"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200


def test_internal_user_without_institution_reads_any_document(app, client):
    # INTERNAL_USER is also a platform-review role => unrestricted with null institution.
    document = _build_owned_document(title="Any student SOP", owner_institution_id=uuid4())
    db = _ScopedFakeDB([document], mentor_institution_id=None)

    async def override_current_user():
        user = _fake_user({"document.mentor.review"}, role=UserRole.INTERNAL_USER)
        user.institution_id = None
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    response = client.get(
        f"/api/v1/mentor/documents/{document.id}",
        headers={"Authorization": "Bearer fake"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200


def test_mentor_with_null_institution_cannot_read_real_institution_document(app, client):
    # H5 residual: a plain MENTOR with institution_id=None must NOT be treated as
    # an unrestricted platform reviewer. It is institution-scoped (to the null
    # cohort), so a real-institution student's doc is invisible => 404.
    document = _build_owned_document(title="Other institution SOP", owner_institution_id=uuid4())
    db = _ScopedFakeDB([document], mentor_institution_id=None)

    async def override_current_user():
        user = _fake_user({"document.mentor.review"}, role=UserRole.MENTOR)
        user.institution_id = None
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    response = client.get(
        f"/api/v1/mentor/documents/{document.id}",
        headers={"Authorization": "Bearer fake"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_mentor_with_null_institution_cannot_submit_feedback_on_real_institution_document(app, client):
    # Same H5 residual on the write path: null-institution MENTOR cannot write
    # feedback on a real-institution student's doc, and nothing is committed.
    document = _build_owned_document(title="Other institution SOP", owner_institution_id=uuid4())
    db = _ScopedFakeDB([document], mentor_institution_id=None)

    async def override_current_user():
        user = _fake_user({"document.mentor.submit"}, role=UserRole.MENTOR)
        user.institution_id = None
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    response = client.post(
        f"/api/v1/mentor/documents/{document.id}/feedback",
        json={
            "summary": "A valid looking summary with sufficient length for schema requirements.",
            "strengths": ["One"],
            "revision_priorities": ["Two"],
            "caution_notes": [],
        },
        headers={"Authorization": "Bearer fake"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert db.committed is False


def test_mentor_cannot_submit_feedback_outside_their_institution(app, client):
    mentor_inst = uuid4()
    document = _build_owned_document(title="Other institution SOP", owner_institution_id=uuid4())
    db = _ScopedFakeDB([document], mentor_institution_id=mentor_inst)

    async def override_current_user():
        user = _fake_user({"document.mentor.submit"})
        user.institution_id = mentor_inst
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db
    response = client.post(
        f"/api/v1/mentor/documents/{document.id}/feedback",
        json={
            "summary": "A valid looking summary with sufficient length for schema requirements.",
            "strengths": ["One"],
            "revision_priorities": ["Two"],
            "caution_notes": [],
        },
        headers={"Authorization": "Bearer fake"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert db.committed is False


def test_mentor_routes_return_403_without_mentor_capabilities(app, client):
    pending = _build_document(title="Restricted document", has_human_review=False)
    db = _FakeDB([pending])

    async def override_current_user():
        return _fake_user({"profile.self.read"})

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    list_response = client.get(
        "/api/v1/mentor/pending-reviews",
        headers={"Authorization": "Bearer fake"},
    )
    submit_response = client.post(
        f"/api/v1/mentor/documents/{pending.id}/feedback",
        json={
            "summary": "A valid looking summary with sufficient length for schema requirements.",
            "strengths": ["One"],
            "revision_priorities": ["Two"],
            "caution_notes": [],
        },
        headers={"Authorization": "Bearer fake"},
    )

    app.dependency_overrides.clear()

    assert list_response.status_code == 403
    assert submit_response.status_code == 403
    assert list_response.json()["error"]["code"] == "auth_insufficient_permissions"
    assert submit_response.json()["error"]["code"] == "auth_insufficient_permissions"
