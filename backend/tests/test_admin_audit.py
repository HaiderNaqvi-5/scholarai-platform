from uuid import uuid4

from fastapi import Request

from app.core.security import create_access_token
from app.services.audit_service import AuditService


def make_request(*, headers: dict[str, str] | None = None) -> Request:
    header_items = []
    for key, value in (headers or {}).items():
        header_items.append((key.lower().encode("utf-8"), value.encode("utf-8")))

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": header_items,
            "client": ("127.0.0.1", 1234),
        }
    )


def test_build_admin_route_metadata_for_scholarship_create():
    service = AuditService()

    metadata = service.build_admin_route_metadata(
        "/api/v1/admin/scholarships",
        "POST",
        {},
        response_payload={"id": "sch-1"},
    )

    assert metadata == {
        "action": "create_scholarship",
        "target_table": "scholarships",
        "target_id": "sch-1",
    }


def test_build_admin_route_metadata_for_scholarship_update():
    service = AuditService()
    scholarship_id = uuid4()

    metadata = service.build_admin_route_metadata(
        f"/api/v1/admin/scholarships/{scholarship_id}",
        "PATCH",
        {"scholarship_id": scholarship_id},
    )

    assert metadata == {
        "action": "update_scholarship",
        "target_table": "scholarships",
        "target_id": str(scholarship_id),
    }


def test_extract_admin_id_from_bearer_token():
    service = AuditService()
    admin_id = uuid4()
    token = create_access_token({"sub": str(admin_id), "role": "admin"})
    request = make_request(headers={"Authorization": f"Bearer {token}"})

    assert service.extract_admin_id(request) == admin_id
