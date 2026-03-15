from app.demo.demo_dataset import DEMO_DATASET_VERSION, SCHOLARSHIP_SEED
from app.models import RecordState


def test_demo_seed_covers_published_and_internal_states():
    assert DEMO_DATASET_VERSION == "mvp-demo-2026-03"

    published = [
        record for record in SCHOLARSHIP_SEED if record["record_state"] == RecordState.PUBLISHED
    ]
    validated = [
        record for record in SCHOLARSHIP_SEED if record["record_state"] == RecordState.VALIDATED
    ]
    raw = [record for record in SCHOLARSHIP_SEED if record["record_state"] == RecordState.RAW]

    assert len(published) >= 4
    assert len(validated) >= 1
    assert len(raw) >= 1
    assert all("daad" not in record["title"].lower() for record in SCHOLARSHIP_SEED)
    assert all(record["country_code"] in {"CA", "US"} for record in SCHOLARSHIP_SEED)
    assert all(
        record["country_code"] != "US" or "fulbright" in record["title"].lower()
        for record in SCHOLARSHIP_SEED
    )
