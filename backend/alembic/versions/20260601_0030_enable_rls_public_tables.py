"""enable RLS on all public tables (Supabase security lints 0013 + 0023)

Closes Supabase advisor lints:
  - 0013_rls_disabled_in_public  (39 tables)
  - 0023_sensitive_columns_exposed (interview_kpi_snapshots, interview_responses)

The backend connects as the pooler ``postgres`` role (bypassrls), so enabling
RLS with no policies is deny-all to the PostgREST ``anon``/``authenticated``
roles only and has zero effect on application access. No ``auth.uid()``
policies are added: this app uses Clerk / local auth (not Supabase Auth JWTs)
and never touches the Data API, so ownership predicates would be inert.

An ``ddl_command_end`` event trigger auto-enables RLS on any future public
table. ``CREATE EVENT TRIGGER`` requires superuser; on hosted Supabase the
``postgres`` role is not superuser, so the trigger creation is guarded and
skipped with a NOTICE if the privilege is missing. The table fix always
applies regardless.

Revision ID: 20260601_0030
Revises: 20260526_0029
Create Date: 2026-06-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260601_0030"
down_revision: Union[str, None] = "20260526_0029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# All 39 public tables flagged by the Supabase linter.
RLS_TABLES: tuple[str, ...] = (
    "alembic_version",
    "scholarship_requirements",
    "applications",
    "audit_logs",
    "documents",
    "document_feedback",
    "interview_sessions",
    "interview_responses",
    "scholarship_chunks",
    "capabilities",
    "role_capabilities",
    "scholarships",
    "user_capabilities",
    "user_institution_access",
    "ingestion_runs",
    "recommendation_kpi_snapshots",
    "document_kpi_snapshots",
    "interview_kpi_snapshots",
    "waitlist",
    "institutions",
    "institution_students",
    "referral_enrollments",
    "application_tracker_items",
    "universities",
    "visa_interview_questions",
    "consent_audit_log",
    "data_export_requests",
    "data_deletion_requests",
    "university_leads",
    "legal_documents",
    "student_profiles",
    "source_feed",
    "source_registry",
    "sop_monthly_usage",
    "usage_ledger",
    "invite_codes",
    "email_verifications",
    "password_resets",
    "users",
)


def upgrade() -> None:
    # 1. Enable RLS + revoke Data API roles on every flagged table (idempotent).
    for table in RLS_TABLES:
        op.execute(f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY;')
        op.execute(f'REVOKE ALL ON public."{table}" FROM anon, authenticated;')

    # 2. Regression guard: auto-enable RLS on any newly created public table.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.auto_enable_rls()
            RETURNS event_trigger
            LANGUAGE plpgsql
            SET search_path = ''
        AS $fn$
        DECLARE
            obj record;
        BEGIN
            FOR obj IN
                SELECT object_identity
                FROM pg_event_trigger_ddl_commands()
                WHERE command_tag = 'CREATE TABLE'
                  AND schema_name = 'public'
            LOOP
                EXECUTE format(
                    'ALTER TABLE %s ENABLE ROW LEVEL SECURITY;', obj.object_identity
                );
                EXECUTE format(
                    'REVOKE ALL ON %s FROM anon, authenticated;', obj.object_identity
                );
            END LOOP;
        END;
        $fn$;
        """
    )

    # CREATE EVENT TRIGGER needs superuser. Hosted Supabase 'postgres' is not
    # superuser -> guard so the migration still succeeds (table fix is what matters).
    op.execute(
        """
        DO $guard$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_event_trigger WHERE evtname = 'auto_enable_rls_trg'
            ) THEN
                CREATE EVENT TRIGGER auto_enable_rls_trg
                    ON ddl_command_end
                    WHEN TAG IN ('CREATE TABLE')
                    EXECUTE FUNCTION public.auto_enable_rls();
            END IF;
        EXCEPTION WHEN insufficient_privilege THEN
            RAISE NOTICE 'auto_enable_rls_trg not created (needs superuser); '
                         'table-level RLS still applied. Enable RLS manually on '
                         'new public tables, or run this as a privileged role.';
        END;
        $guard$;
        """
    )


def downgrade() -> None:
    # Drop the guard first.
    op.execute("DROP EVENT TRIGGER IF EXISTS auto_enable_rls_trg;")
    op.execute("DROP FUNCTION IF EXISTS public.auto_enable_rls();")

    # Disable RLS. Intentionally does NOT re-GRANT anon/authenticated: re-opening
    # the Data API hole on downgrade would defeat the security purpose. Grant
    # explicitly if a future table genuinely needs Data API exposure.
    for table in RLS_TABLES:
        op.execute(f'ALTER TABLE public."{table}" DISABLE ROW LEVEL SECURITY;')
