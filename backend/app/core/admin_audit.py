from __future__ import annotations

import logging
from typing import Any

from fastapi import Request, Response
from fastapi.routing import APIRoute

from app.core.database import async_session_factory
from app.models.models import Scholarship
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)
audit_service = AuditService()


class AdminAuditRoute(APIRoute):
    """Audit successful admin mutations after the route handler completes."""

    def get_route_handler(self):
        original_route_handler = super().get_route_handler()

        async def audited_route_handler(request: Request) -> Response:
            context = await _build_audit_context(request)
            response = await original_route_handler(request)
            try:
                await _log_audit_event(request, response, context)
            except Exception:
                logger.exception("Admin audit logging failed")
            return response

        return audited_route_handler


async def _build_audit_context(request: Request) -> dict[str, Any] | None:
    metadata = audit_service.build_admin_route_metadata(
        request.url.path,
        request.method,
        request.path_params,
    )
    if not metadata:
        return None

    context = {
        "admin_id": audit_service.extract_admin_id(request),
        "request_payload": audit_service.parse_json_bytes(await request.body()),
        "old_value": None,
    }
    context.update(metadata)

    if metadata["target_table"] == "scholarships" and metadata["target_id"]:
        async with async_session_factory() as db:
            scholarship = await db.get(Scholarship, audit_service.coerce_uuid(metadata["target_id"]))
            if scholarship is not None:
                context["old_value"] = audit_service.snapshot(scholarship)

    return context


async def _log_audit_event(
    request: Request,
    response: Response,
    context: dict[str, Any] | None,
) -> None:
    if not context or response.status_code >= 400:
        return

    response_payload = audit_service.parse_json_bytes(getattr(response, "body", b""))
    metadata = audit_service.build_admin_route_metadata(
        request.url.path,
        request.method,
        request.path_params,
        response_payload=response_payload,
    )
    if not metadata:
        return

    new_value = response_payload
    if metadata["target_table"] == "scholarships" and metadata["target_id"] and request.method != "DELETE":
        async with async_session_factory() as db:
            scholarship = await db.get(Scholarship, audit_service.coerce_uuid(metadata["target_id"]))
            if scholarship is not None:
                new_value = audit_service.snapshot(scholarship)

    async with async_session_factory() as db:
        await audit_service.log_event(
            db,
            admin_id=context["admin_id"],
            action=metadata["action"],
            target_table=metadata["target_table"],
            target_id=metadata["target_id"],
            old_value=context["old_value"],
            new_value=new_value,
            ip_address=audit_service.get_request_ip(request),
        )
        await db.commit()
