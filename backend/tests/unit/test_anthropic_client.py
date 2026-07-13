"""Unit tests for app.services.llm.anthropic_client JSON extraction fallback."""

import logging

from app.services.llm.anthropic_client import _extract_json_object


def test_extract_json_object_logs_warning_on_unparseable_input(caplog):
    """When the model output has no JSON object at all, the extractor must
    log a WARNING (operator signal) instead of silently returning {}."""
    raw = "The model refused to answer with structured data."

    with caplog.at_level(logging.WARNING):
        result = _extract_json_object(raw)

    assert result == {}
    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warning_records, "expected a WARNING log record on unparseable JSON"
    assert any("anthropic.json_parse_failed" in r.message for r in warning_records)
