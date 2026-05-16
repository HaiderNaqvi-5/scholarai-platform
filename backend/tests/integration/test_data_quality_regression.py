"""Data-quality regression guards tied to publication rules.

These pin the invariants that keep the public scholarship surface trustworthy:
ingested data lands as RAW (never auto-published), the public route is
published-only, and provenance is preserved on every record.
"""

import pytest

from app.models import RecordState, Scholarship
from app.schemas.curation import CurationRawImportRequest
from app.services.ingestion.service import ParsedScholarshipCandidate


def test_ingestion_import_request_cannot_set_publication_state():
    # The raw-import contract exposes no record_state / published field, so an
    # ingestion run physically cannot push a record straight to PUBLISHED.
    forbidden = {"record_state", "published", "published_at", "is_published"}
    assert forbidden.isdisjoint(CurationRawImportRequest.model_fields)


def test_parsed_candidate_carries_no_publication_state():
    # A parsed scholarship candidate likewise carries no publication state.
    forbidden = {"record_state", "published", "published_at"}
    assert forbidden.isdisjoint(ParsedScholarshipCandidate.model_fields)


def test_scholarship_record_state_defaults_to_raw():
    # New scholarship rows default to RAW — curator review is mandatory before
    # anything reaches the published-only public surface.
    assert Scholarship.__table__.c.record_state.default.arg is RecordState.RAW


def test_public_scholarships_route_is_published_only():
    # The public list + detail routes both constrain on record_state == PUBLISHED.
    import inspect

    import app.api.v1.routes.scholarships as scholarships_route

    source = inspect.getsource(scholarships_route)
    assert "RecordState.PUBLISHED" in source
    # the public list query must filter on it
    list_src = inspect.getsource(scholarships_route.list_scholarships)
    assert "record_state == RecordState.PUBLISHED" in list_src
    detail_src = inspect.getsource(scholarships_route.get_scholarship)
    assert "record_state == RecordState.PUBLISHED" in detail_src


@pytest.mark.parametrize("provenance_field", ["source_url", "content_hash", "provenance_payload"])
def test_scholarship_retains_provenance_columns(provenance_field):
    # Provenance columns must exist so any published record can be traced back
    # to its ingestion source/run via /scholarships/{id}/provenance.
    assert provenance_field in Scholarship.__table__.c
