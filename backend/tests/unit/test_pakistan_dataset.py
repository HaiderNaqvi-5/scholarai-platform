"""Sanity tests for the Pakistan-pivot seed dataset (Feature 3)."""

from app.demo.pakistan_dataset import (
    PAKISTAN_SCHOLARSHIP_SEED,
    PAKISTAN_SOURCE_REGISTRY_SEED,
)
from app.models import RecordState


def test_seed_includes_tier1_scholarships() -> None:
    titles = {entry["title"] for entry in PAKISTAN_SCHOLARSHIP_SEED}
    for required in (
        "Chevening Scholarship",
        "Fulbright Foreign Student Program (Pakistan)",
        "DAAD Scholarships (Pakistan)",
        "Commonwealth Scholarship (Pakistan)",
        "HEC Overseas Scholarship for PhD",
    ):
        assert required in titles


def test_seed_has_at_least_twenty_records() -> None:
    # 5 Tier 1 + 5 Tier 2 + 10 GTA/GRA = 20
    assert len(PAKISTAN_SCHOLARSHIP_SEED) >= 20


def test_every_seed_row_open_to_pakistani_nationals() -> None:
    for entry in PAKISTAN_SCHOLARSHIP_SEED:
        assert "PK" in entry["citizenship_rules"], entry["title"]


def test_every_seed_row_published_immediately() -> None:
    for entry in PAKISTAN_SCHOLARSHIP_SEED:
        assert entry["record_state"] == RecordState.PUBLISHED, entry["title"]


def test_gta_gra_funding_type_present() -> None:
    funding_types = {entry["funding_type"] for entry in PAKISTAN_SCHOLARSHIP_SEED}
    assert "gta_gra" in funding_types


def test_every_seed_source_key_resolves() -> None:
    valid_keys = {entry["source_key"] for entry in PAKISTAN_SOURCE_REGISTRY_SEED}
    for entry in PAKISTAN_SCHOLARSHIP_SEED:
        assert entry["source_key"] in valid_keys, entry["title"]


def test_source_urls_are_unique() -> None:
    urls = [entry["source_url"] for entry in PAKISTAN_SCHOLARSHIP_SEED]
    assert len(urls) == len(set(urls))
