import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import create_app


@pytest.fixture
def app():
    application = create_app()
    try:
        yield application
    finally:
        application.dependency_overrides.clear()


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
