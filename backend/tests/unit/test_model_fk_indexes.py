"""P2-7: every unindexed FK column listed in the audit must have a single-column index.

Pure ORM introspection (Table.indexes) — no DB connection required.
"""
from app.models.models import (
    Application,
    ApplicationTrackerItem,
    AuditLog,
    DocumentRecord,
    IngestionRun,
    InterviewSession,
    RoleCapability,
    Scholarship,
    ScholarshipChunk,
    ScholarshipRequirement,
    UniversityLead,
)

# table -> FK columns from the P2-7 audit that must each have a single-column index
EXPECTED: dict = {
    Scholarship.__table__: [
        "reviewed_by_user_id",
        "validated_by_user_id",
        "published_by_user_id",
        "source_registry_id",
    ],
    IngestionRun.__table__: ["triggered_by_user_id"],
    AuditLog.__table__: ["actor_user_id"],
    ScholarshipRequirement.__table__: ["scholarship_id"],
    ScholarshipChunk.__table__: ["scholarship_id"],
    DocumentRecord.__table__: ["scholarship_id"],
    InterviewSession.__table__: ["scholarship_id"],
    ApplicationTrackerItem.__table__: ["scholarship_id", "university_id"],
    Application.__table__: ["scholarship_id"],
    RoleCapability.__table__: ["granted_by"],
    UniversityLead.__table__: ["consent_audit_log_id"],
}


def test_all_listed_fks_have_a_single_column_index():
    for table, cols in EXPECTED.items():
        single_col_indexed = {
            ix.columns.keys()[0]
            for ix in table.indexes
            if len(ix.columns) == 1
        }
        for col in cols:
            assert col in single_col_indexed, (
                f"{table.name}.{col} has no single-column index"
            )
