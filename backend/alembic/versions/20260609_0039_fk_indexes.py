"""Index every unindexed foreign key (P2-7).

FKs used in joins/filters (reviewer/validator/publisher lookups, cascade
deletes on scholarship_id, actor/triggered-by audit lookups, granted_by,
consent_audit_log_id) had no supporting index, forcing sequential scans.
Adds a single-column btree index on each.

Revision ID: 20260609_0039
Revises: 20260609_0038
Create Date: 2026-06-09 00:39:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260609_0039"
down_revision: Union[str, None] = "20260609_0038"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (index_name, table_name, column_name)
INDEXES = [
    ("ix_scholarships_reviewed_by_user_id", "scholarships", "reviewed_by_user_id"),
    ("ix_scholarships_validated_by_user_id", "scholarships", "validated_by_user_id"),
    ("ix_scholarships_published_by_user_id", "scholarships", "published_by_user_id"),
    ("ix_scholarships_source_registry_id", "scholarships", "source_registry_id"),
    ("ix_ingestion_runs_triggered_by_user_id", "ingestion_runs", "triggered_by_user_id"),
    ("ix_audit_logs_actor_user_id", "audit_logs", "actor_user_id"),
    ("ix_scholarship_requirements_scholarship_id", "scholarship_requirements", "scholarship_id"),
    ("ix_scholarship_chunks_scholarship_id", "scholarship_chunks", "scholarship_id"),
    ("ix_documents_scholarship_id", "documents", "scholarship_id"),
    ("ix_interview_sessions_scholarship_id", "interview_sessions", "scholarship_id"),
    ("ix_application_tracker_items_scholarship_id", "application_tracker_items", "scholarship_id"),
    ("ix_application_tracker_items_university_id", "application_tracker_items", "university_id"),
    ("ix_applications_scholarship_id", "applications", "scholarship_id"),
    ("ix_role_capabilities_granted_by", "role_capabilities", "granted_by"),
    ("ix_university_leads_consent_audit_log_id", "university_leads", "consent_audit_log_id"),
]


def upgrade() -> None:
    for index_name, table_name, column_name in INDEXES:
        op.create_index(index_name, table_name, [column_name])


def downgrade() -> None:
    for index_name, table_name, _column_name in reversed(INDEXES):
        op.drop_index(index_name, table_name=table_name)
