import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import get_role_capabilities
from app.models import AuditLog, Capability, RoleCapability, User, UserCapability, UserRole
from app.schemas.access_control import (
    AccessControlManagedUser,
    AccessControlManagedUserListResponse,
    AccessControlRoleChangeItem,
    AccessControlRoleChangeListResponse,
)


class AccessControlService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_managed_users(self) -> AccessControlManagedUserListResponse:
        result = await self.db.execute(
            select(User).order_by(User.created_at.desc(), User.email.asc())
        )
        users = result.scalars().all()
        if not users:
            return AccessControlManagedUserListResponse(items=[], total=0)

        # Bulk-fetch role capabilities for all distinct roles in one query.
        distinct_roles = {user.role for user in users}
        role_caps_result = await self.db.execute(
            select(RoleCapability.role, Capability.capability_key)
            .join(Capability, RoleCapability.capability_id == Capability.id)
            .where(Capability.is_active.is_(True))
            .where(RoleCapability.role.in_(distinct_roles))
        )
        role_capabilities_map: dict[UserRole, set[str]] = {}
        for role, cap_key in role_caps_result.all():
            role_capabilities_map.setdefault(role, set()).add(cap_key)

        # Bulk-fetch user-specific non-expired capabilities for all users in one query.
        user_ids = [user.id for user in users]
        now_utc = datetime.now(timezone.utc)
        user_caps_result = await self.db.execute(
            select(UserCapability.user_id, Capability.capability_key)
            .join(Capability, UserCapability.capability_id == Capability.id)
            .where(Capability.is_active.is_(True))
            .where(UserCapability.user_id.in_(user_ids))
            .where(
                (UserCapability.expires_at.is_(None))
                | (UserCapability.expires_at > now_utc)
            )
        )
        user_capabilities_map: dict[uuid.UUID, set[str]] = {}
        for user_id, cap_key in user_caps_result.all():
            user_capabilities_map.setdefault(user_id, set()).add(cap_key)

        # Compute effective capabilities in memory (no further DB queries).
        items: list[AccessControlManagedUser] = []
        for user in users:
            role_caps = role_capabilities_map.get(user.role, set())
            effective_role_caps = role_caps or set(get_role_capabilities(user.role))
            user_caps = user_capabilities_map.get(user.id, set())
            capabilities = sorted(effective_role_caps | user_caps)
            items.append(
                AccessControlManagedUser(
                    user_id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    role=user.role,
                    is_active=user.is_active,
                    auth_token_version=user.auth_token_version,
                    effective_capabilities=capabilities,
                )
            )
        return AccessControlManagedUserListResponse(items=items, total=len(items))

    async def update_user_role(
        self,
        *,
        actor_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
        role: UserRole,
        reason: str | None,
    ) -> AccessControlRoleChangeItem:
        target = await self._load_target_user(target_user_id)
        previous_role = target.role
        if previous_role == role:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Target user already has this role",
            )

        target.role = role
        target.auth_token_version += 1
        await self.db.flush()

        audit = AuditLog(
            actor_user_id=actor_user_id,
            entity_type="user",
            entity_id=str(target.id),
            action="access_control.role.update",
            before_data={
                "role": previous_role.value,
                "auth_token_version": target.auth_token_version - 1,
                "capabilities": sorted(get_role_capabilities(previous_role)),
            },
            after_data={
                "role": role.value,
                "auth_token_version": target.auth_token_version,
                "capabilities": sorted(get_role_capabilities(role)),
                "reason": reason,
            },
        )
        self.db.add(audit)
        await self.db.flush()

        return AccessControlRoleChangeItem(
            audit_id=audit.id,
            target_user_id=target.id,
            actor_user_id=audit.actor_user_id,
            action="access_control.role.update",
            previous_role=previous_role,
            next_role=role,
            reason=reason,
            changed_at=audit.created_at,
            reverted_by_audit_id=None,
            is_reversible=True,
        )

    async def revert_role_change(
        self,
        *,
        actor_user_id: uuid.UUID,
        audit_id: uuid.UUID,
        reason: str | None,
    ) -> AccessControlRoleChangeItem:
        audit = await self._load_role_update_audit(audit_id)
        reverted_by = await self._find_revert_audit(audit.id)
        if reverted_by is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role change is already reverted",
            )

        target_user_id = self._extract_uuid(audit.entity_id)
        target = await self._load_target_user(target_user_id)
        previous_role = self._extract_role(audit.before_data, "role")
        current_role = target.role
        target.role = previous_role
        target.auth_token_version += 1
        await self.db.flush()

        revert_audit = AuditLog(
            actor_user_id=actor_user_id,
            entity_type="user",
            entity_id=str(target.id),
            action="access_control.role.revert",
            before_data={
                "role": current_role.value,
                "auth_token_version": target.auth_token_version - 1,
                "reverted_audit_id": str(audit.id),
            },
            after_data={
                "role": previous_role.value,
                "auth_token_version": target.auth_token_version,
                "reason": reason,
                "reverted_audit_id": str(audit.id),
            },
        )
        self.db.add(revert_audit)
        await self.db.flush()

        original_next_role = self._extract_role(audit.after_data, "role")
        return AccessControlRoleChangeItem(
            audit_id=audit.id,
            target_user_id=target.id,
            actor_user_id=audit.actor_user_id,
            action="access_control.role.update",
            previous_role=previous_role,
            next_role=original_next_role,
            reason=(audit.after_data or {}).get("reason") if isinstance(audit.after_data, dict) else None,
            changed_at=audit.created_at,
            reverted_by_audit_id=revert_audit.id,
            is_reversible=False,
        )

    async def list_role_changes(
        self,
        *,
        target_user_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> AccessControlRoleChangeListResponse:
        query = (
            select(AuditLog)
            .where(
                AuditLog.entity_type == "user",
                AuditLog.action == "access_control.role.update",
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        if target_user_id is not None:
            query = query.where(AuditLog.entity_id == str(target_user_id))

        result = await self.db.execute(query)
        audits = result.scalars().all()

        # Batch-load any revert audits that reference these update audits to avoid N+1 queries.
        reverted_by_map: dict[uuid.UUID, AuditLog] = {}
        audit_ids = [audit.id for audit in audits]
        if audit_ids:
            audit_id_strs = [str(aid) for aid in audit_ids]
            revert_query = select(AuditLog).where(
                AuditLog.entity_type == "user",
                AuditLog.action == "access_control.role.revert",
                AuditLog.before_data["reverted_audit_id"].as_string().in_(audit_id_strs),
            )
            revert_result = await self.db.execute(revert_query)
            for revert_audit in revert_result.scalars().all():
                if isinstance(revert_audit.before_data, dict):
                    ref_id_str = revert_audit.before_data.get("reverted_audit_id")
                    if ref_id_str:
                        try:
                            reverted_by_map[uuid.UUID(ref_id_str)] = revert_audit
                        except ValueError:
                            pass

        items: list[AccessControlRoleChangeItem] = []
        for audit in audits:
            reverted_by = reverted_by_map.get(audit.id)
            previous_role = self._extract_role(audit.before_data, "role")
            next_role = self._extract_role(audit.after_data, "role")
            items.append(
                AccessControlRoleChangeItem(
                    audit_id=audit.id,
                    target_user_id=self._extract_uuid(audit.entity_id),
                    actor_user_id=audit.actor_user_id,
                    action="access_control.role.update",
                    previous_role=previous_role,
                    next_role=next_role,
                    reason=(audit.after_data or {}).get("reason")
                    if isinstance(audit.after_data, dict)
                    else None,
                    changed_at=audit.created_at,
                    reverted_by_audit_id=reverted_by.id if reverted_by is not None else None,
                    is_reversible=reverted_by is None,
                )
            )
        return AccessControlRoleChangeListResponse(items=items, total=len(items))

    async def _load_target_user(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        target = result.scalar_one_or_none()
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return target

    async def _load_role_update_audit(self, audit_id: uuid.UUID) -> AuditLog:
        result = await self.db.execute(
            select(AuditLog).where(
                AuditLog.id == audit_id,
                AuditLog.entity_type == "user",
                AuditLog.action == "access_control.role.update",
            )
        )
        audit = result.scalar_one_or_none()
        if audit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role update audit record not found",
            )
        return audit

    async def _find_revert_audit(self, audit_id: uuid.UUID) -> AuditLog | None:
        result = await self.db.execute(
            select(AuditLog)
            .where(
                AuditLog.entity_type == "user",
                AuditLog.action == "access_control.role.revert",
                AuditLog.before_data["reverted_audit_id"].as_string() == str(audit_id),
            )
            .order_by(AuditLog.created_at.desc())
            .limit(1)
        )
        return result.scalars().one_or_none()

    def _extract_uuid(self, value: str) -> uuid.UUID:
        try:
            return uuid.UUID(value)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid audit user identifier",
            ) from exc

    def _extract_role(self, payload: dict | None, key: str) -> UserRole:
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid audit payload",
            )
        role_value = payload.get(key)
        try:
            return UserRole(str(role_value))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid role in audit payload",
            ) from exc
