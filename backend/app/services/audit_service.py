from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect as sqlalchemy_inspect

from app.core.security import decode_token
from app.models.models import AuditLog


class AuditService:
    """Persist audit rows for admin actions."""

    async def log_event(
        self,
        db: AsyncSession,
        *,
        admin_id: UUID | None,
        action: str,
        target_table: str | None,
        target_id: str | None = None,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            admin_id=admin_id,
            action=action,
            target_table=target_table,
            target_id=target_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        db.add(audit_log)
        await db.flush()
        return audit_log

    def snapshot(
        self,
        instance: Any,
        *,
        include: Iterable[str] | None = None,
        exclude: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        include_set = set(include or [])
        exclude_set = set(exclude or [])
        filter_include = bool(include_set)

        snapshot: dict[str, Any] = {}
        mapper = sqlalchemy_inspect(instance.__class__)
        for column in mapper.columns:
            key = column.key
            if filter_include and key not in include_set:
                continue
            if key in exclude_set:
                continue
            snapshot[key] = self.serialize(getattr(instance, key))
        return snapshot

    def build_admin_route_metadata(
        self,
        path: str,
        method: str,
        path_params: dict[str, Any],
        *,
        response_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if method not in {"POST", "PATCH", "DELETE"}:
            return None

        if path.endswith("/admin/scholarships") and method == "POST":
            return {
                "action": "create_scholarship",
                "target_table": "scholarships",
                "target_id": self.serialize((response_payload or {}).get("id")),
            }

        if "/admin/scholarships/" in path and method in {"PATCH", "DELETE"}:
            return {
                "action": f"{'update' if method == 'PATCH' else 'delete'}_scholarship",
                "target_table": "scholarships",
                "target_id": self.serialize(path_params.get("scholarship_id")),
            }

        if path.endswith("/admin/scraper/trigger") and method == "POST":
            return {
                "action": "trigger_scraper",
                "target_table": "scraper_runs",
                "target_id": self.serialize((response_payload or {}).get("task_id")),
            }

        return None

    def extract_admin_id(self, request: Request) -> UUID | None:
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return None

        token = authorization.removeprefix("Bearer ").strip()
        if not token:
            return None

        try:
            payload = decode_token(token)
        except Exception:
            return None

        subject = payload.get("sub")
        if not subject:
            return None

        try:
            return UUID(str(subject))
        except ValueError:
            return None

    @staticmethod
    def coerce_uuid(value: Any) -> UUID | Any:
        if value is None or isinstance(value, UUID):
            return value

        try:
            return UUID(str(value))
        except ValueError:
            return value

    @staticmethod
    def parse_json_bytes(payload: bytes | str | None) -> Any:
        if not payload:
            return None

        if isinstance(payload, bytes):
            text = payload.decode("utf-8", errors="ignore").strip()
        else:
            text = payload.strip()

        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def get_request_ip(request: Request) -> str | None:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else None

    @classmethod
    def serialize(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, list):
            return [cls.serialize(item) for item in value]
        if isinstance(value, dict):
            return {str(key): cls.serialize(item) for key, item in value.items()}
        return str(value)
