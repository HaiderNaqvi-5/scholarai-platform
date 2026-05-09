# backend/tests/unit/test_logging_smoke.py
"""When third-party integrations fail, services must emit a structured
warning, not a bare print. Captures the loggers used by each service."""

import logging
import pytest

EXPECTED_LOGGERS = [
    "app.services.recommendations.service",
    "app.services.recommendations.hybrid_retriever",
    "app.services.documents.service",
    "app.services.documents.retriever",
    "app.services.interview.service",
    "app.services.ingestion.service",
]


@pytest.mark.parametrize("logger_name", EXPECTED_LOGGERS)
def test_service_module_has_named_logger(logger_name):
    """Every service module must register a logger with its dotted module name."""
    import importlib
    module = importlib.import_module(logger_name)
    found = False
    for value in vars(module).values():
        if isinstance(value, logging.Logger) and value.name == logger_name:
            found = True
            break
    assert found, (
        f"{logger_name} must define a module-level logger via "
        f"`logger = logging.getLogger(__name__)`"
    )
