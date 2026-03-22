"""add rbac capability and institution scope tables

Revision ID: 20260321_0009
Revises: 20260321_0008
Create Date: 2026-03-21 18:30:00
"""

# pyright: reportUnknownArgumentType=false, reportUnknownVariableType=false, reportMissingTypeArgument=false

from datetime import datetime, timezone
from typing import cast
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260321_0009"
down_revision = "20260321_0008"
branch_labels = None
depends_on = None


def _add_user_role_values() -> None:
    with op.get_context().autocommit_block():
        for enum_value in [
            "enduser_student",
            "internal_user",
            "dev",
            "university",
            "owner",
        ]:
            op.execute(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_enum e
                        JOIN pg_type t ON e.enumtypid = t.oid
                        WHERE t.typname = 'user_role'
                          AND e.enumlabel = '{enum_value}'
                    ) THEN
                        ALTER TYPE user_role ADD VALUE '{enum_value}';
                    END IF;
                END
                $$;
                """
            )


def _seed_capabilities() -> None:
    now = datetime.now(timezone.utc)

    capability_rows: list[dict[str, object]] = [
        {
            "id": uuid.uuid4(),
            "capability_key": "auth.session.read",
            "resource": "auth",
            "action": "session_read",
            "risk_tier": "low",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "auth.session.refresh",
            "resource": "auth",
            "action": "session_refresh",
            "risk_tier": "low",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "scholarship.public.read",
            "resource": "scholarship",
            "action": "public_read",
            "risk_tier": "low",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "profile.self.read",
            "resource": "profile",
            "action": "self_read",
            "risk_tier": "low",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "profile.self.write",
            "resource": "profile",
            "action": "self_write",
            "risk_tier": "medium",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "saved_opportunity.self.read",
            "resource": "saved_opportunity",
            "action": "self_read",
            "risk_tier": "low",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "saved_opportunity.self.write",
            "resource": "saved_opportunity",
            "action": "self_write",
            "risk_tier": "low",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "recommendation.self.generate",
            "resource": "recommendation",
            "action": "self_generate",
            "risk_tier": "low",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "document.self.read",
            "resource": "document",
            "action": "self_read",
            "risk_tier": "low",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "document.self.create",
            "resource": "document",
            "action": "self_create",
            "risk_tier": "low",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "document.self.feedback",
            "resource": "document",
            "action": "self_feedback",
            "risk_tier": "medium",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "document.mentor.review",
            "resource": "document",
            "action": "mentor_review",
            "risk_tier": "medium",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "document.mentor.submit",
            "resource": "document",
            "action": "mentor_submit",
            "risk_tier": "medium",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "interview.self.create",
            "resource": "interview",
            "action": "self_create",
            "risk_tier": "low",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "interview.self.read",
            "resource": "interview",
            "action": "self_read",
            "risk_tier": "low",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "interview.self.respond",
            "resource": "interview",
            "action": "self_respond",
            "risk_tier": "low",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "curation.queue.read",
            "resource": "curation",
            "action": "queue_read",
            "risk_tier": "medium",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "curation.record.validate",
            "resource": "curation",
            "action": "record_validate",
            "risk_tier": "high",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "curation.record.publish",
            "resource": "curation",
            "action": "record_publish",
            "risk_tier": "critical",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "admin.audit.read",
            "resource": "admin",
            "action": "audit_read",
            "risk_tier": "high",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "admin.ingestion.run",
            "resource": "admin",
            "action": "ingestion_run",
            "risk_tier": "high",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "university.applications.read",
            "resource": "university",
            "action": "applications_read",
            "risk_tier": "high",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "university.students.read",
            "resource": "university",
            "action": "students_read",
            "risk_tier": "high",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "owner.system.read",
            "resource": "owner",
            "action": "system_read",
            "risk_tier": "critical",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "capability_key": "owner.system.control",
            "resource": "owner",
            "action": "system_control",
            "risk_tier": "critical",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    ]

    capabilities_table = sa.table(
        "capabilities",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("capability_key", sa.String()),
        sa.column("resource", sa.String()),
        sa.column("action", sa.String()),
        sa.column("risk_tier", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(capabilities_table, capability_rows)

    capability_id_map = {row["capability_key"]: row["id"] for row in capability_rows}

    role_to_caps: dict[str, list[str]] = {
        "student": [
            "auth.session.read",
            "auth.session.refresh",
            "scholarship.public.read",
            "profile.self.read",
            "profile.self.write",
            "saved_opportunity.self.read",
            "saved_opportunity.self.write",
            "recommendation.self.generate",
            "document.self.read",
            "document.self.create",
            "document.self.feedback",
            "interview.self.create",
            "interview.self.read",
            "interview.self.respond",
        ],
        "enduser_student": [
            "auth.session.read",
            "auth.session.refresh",
            "scholarship.public.read",
            "profile.self.read",
            "profile.self.write",
            "saved_opportunity.self.read",
            "saved_opportunity.self.write",
            "recommendation.self.generate",
            "document.self.read",
            "document.self.create",
            "document.self.feedback",
            "interview.self.create",
            "interview.self.read",
            "interview.self.respond",
        ],
        "internal_user": [
            "auth.session.read",
            "auth.session.refresh",
            "scholarship.public.read",
            "profile.self.read",
            "profile.self.write",
            "saved_opportunity.self.read",
            "saved_opportunity.self.write",
            "recommendation.self.generate",
            "document.self.read",
            "document.self.create",
            "document.self.feedback",
            "interview.self.create",
            "interview.self.read",
            "interview.self.respond",
            "curation.queue.read",
            "admin.audit.read",
            "document.mentor.review",
            "document.mentor.submit",
        ],
        "mentor": [
            "auth.session.read",
            "auth.session.refresh",
            "scholarship.public.read",
            "profile.self.read",
            "profile.self.write",
            "saved_opportunity.self.read",
            "saved_opportunity.self.write",
            "recommendation.self.generate",
            "document.self.read",
            "document.self.create",
            "document.self.feedback",
            "interview.self.create",
            "interview.self.read",
            "interview.self.respond",
            "curation.queue.read",
            "admin.audit.read",
            "document.mentor.review",
            "document.mentor.submit",
        ],
        "dev": [
            "auth.session.read",
            "auth.session.refresh",
            "scholarship.public.read",
            "profile.self.read",
            "profile.self.write",
            "saved_opportunity.self.read",
            "saved_opportunity.self.write",
            "recommendation.self.generate",
            "document.self.read",
            "document.self.create",
            "document.self.feedback",
            "interview.self.create",
            "interview.self.read",
            "interview.self.respond",
            "curation.queue.read",
            "admin.audit.read",
            "document.mentor.review",
            "document.mentor.submit",
            "curation.record.validate",
            "curation.record.publish",
        ],
        "admin": [
            "auth.session.read",
            "auth.session.refresh",
            "scholarship.public.read",
            "profile.self.read",
            "profile.self.write",
            "saved_opportunity.self.read",
            "saved_opportunity.self.write",
            "recommendation.self.generate",
            "document.self.read",
            "document.self.create",
            "document.self.feedback",
            "interview.self.create",
            "interview.self.read",
            "interview.self.respond",
            "curation.queue.read",
            "admin.audit.read",
            "document.mentor.review",
            "document.mentor.submit",
            "curation.record.validate",
            "curation.record.publish",
            "admin.ingestion.run",
        ],
        "university": [
            "university.applications.read",
            "university.students.read",
        ],
        "owner": [
            "auth.session.read",
            "auth.session.refresh",
            "scholarship.public.read",
            "profile.self.read",
            "profile.self.write",
            "saved_opportunity.self.read",
            "saved_opportunity.self.write",
            "recommendation.self.generate",
            "document.self.read",
            "document.self.create",
            "document.self.feedback",
            "interview.self.create",
            "interview.self.read",
            "interview.self.respond",
            "curation.queue.read",
            "admin.audit.read",
            "document.mentor.review",
            "document.mentor.submit",
            "curation.record.validate",
            "curation.record.publish",
            "admin.ingestion.run",
            "university.applications.read",
            "university.students.read",
            "owner.system.read",
            "owner.system.control",
        ],
    }

    role_capability_rows: list[dict[str, object]] = []
    for role_value, capability_keys in role_to_caps.items():
        for capability_key in capability_keys:
            role_capability_rows.append(
                {
                    "role": role_value,
                    "capability_id": capability_id_map[capability_key],
                    "granted_by": None,
                    "created_at": now,
                }
            )

    role_capabilities_table = sa.table(
        "role_capabilities",
        sa.column("role", sa.String()),
        sa.column("capability_id", postgresql.UUID(as_uuid=True)),
        sa.column("granted_by", postgresql.UUID(as_uuid=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(role_capabilities_table, role_capability_rows)


def upgrade() -> None:
    bind = op.get_bind()

    _add_user_role_values()

    capability_risk_tier = postgresql.ENUM(
        "low",
        "medium",
        "high",
        "critical",
        name="capability_risk_tier",
        create_type=False,
    )
    institution_access_level = postgresql.ENUM(
        "viewer",
        "editor",
        "reviewer",
        "admin",
        name="institution_access_level",
        create_type=False,
    )

    capability_risk_tier.create(bind, checkfirst=True)
    institution_access_level.create(bind, checkfirst=True)

    capability_risk_tier_coltype = cast(
        sa.types.TypeEngine,
        postgresql.ENUM(
            "low",
            "medium",
            "high",
            "critical",
            name="capability_risk_tier",
            create_type=False,
        ),
    )
    user_role_coltype = cast(
        sa.types.TypeEngine,
        postgresql.ENUM(
            "student",
            "admin",
            "mentor",
            "enduser_student",
            "internal_user",
            "dev",
            "university",
            "owner",
            name="user_role",
            create_type=False,
        ),
    )
    institution_access_level_coltype = cast(
        sa.types.TypeEngine,
        postgresql.ENUM(
            "viewer",
            "editor",
            "reviewer",
            "admin",
            name="institution_access_level",
            create_type=False,
        ),
    )

    op.create_table(
        "institutions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.add_column("users", sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_users_institution_id", "users", ["institution_id"], unique=False)
    op.create_foreign_key(
        "fk_users_institution_id_institutions",
        "users",
        "institutions",
        ["institution_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "capabilities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("capability_key", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("risk_tier", capability_risk_tier_coltype, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("capability_key"),
    )

    op.create_table(
        "role_capabilities",
        sa.Column("role", user_role_coltype, nullable=False),
        sa.Column("capability_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["capability_id"], ["capabilities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("role", "capability_id"),
    )

    op.create_table(
        "user_capabilities",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("capability_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grant_reason", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["capability_id"], ["capabilities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "capability_id"),
    )

    op.create_table(
        "user_institution_access",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("access_level", institution_access_level_coltype, nullable=False, server_default="viewer"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "institution_id"),
    )
    op.create_index(
        "ix_user_institution_access_institution",
        "user_institution_access",
        ["institution_id"],
        unique=False,
    )

    _seed_capabilities()


def downgrade() -> None:
    op.drop_index("ix_user_institution_access_institution", table_name="user_institution_access")
    op.drop_table("user_institution_access")
    op.drop_table("user_capabilities")
    op.drop_table("role_capabilities")
    op.drop_table("capabilities")

    op.drop_constraint("fk_users_institution_id_institutions", "users", type_="foreignkey")
    op.drop_index("ix_users_institution_id", table_name="users")
    op.drop_column("users", "institution_id")

    op.drop_table("institutions")

    bind = op.get_bind()
    postgresql.ENUM(name="institution_access_level").drop(bind, checkfirst=True)
    postgresql.ENUM(name="capability_risk_tier").drop(bind, checkfirst=True)

    # PostgreSQL enum values on user_role are retained for safety.
