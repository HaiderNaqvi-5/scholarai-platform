from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.models.models import Scholarship
from app.services.audit_service import AuditService


def test_audit_snapshot_serializes_model_values():
    scholarship = Scholarship(
        id=uuid4(),
        name="Test Scholarship",
        country="Germany",
        source_url="https://example.com/scholarship",
        funding_amount_usd=Decimal("1500.50"),
        deadline=date(2026, 9, 1),
    )

    snapshot = AuditService().snapshot(
        scholarship,
        include=["id", "name", "funding_amount_usd", "deadline"],
    )

    assert snapshot == {
        "id": str(scholarship.id),
        "name": "Test Scholarship",
        "funding_amount_usd": 1500.5,
        "deadline": "2026-09-01",
    }
