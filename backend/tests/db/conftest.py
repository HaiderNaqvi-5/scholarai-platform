"""
Synchronous SQLite in-memory fixtures for DB-layer unit tests.

These tests verify ORM column presence and constraints without requiring
a running PostgreSQL instance. The DDL mirrors the target schema after
each migration; update the CREATE TABLE statement when adding columns.

Assumption: full_name is NOT NULL on User (no server default).
"""
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


@pytest.fixture()
def db_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE institutions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                dpa_signed_at TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                clerk_user_id TEXT UNIQUE,
                role TEXT NOT NULL DEFAULT 'student',
                institution_id TEXT REFERENCES institutions(id),
                is_active INTEGER NOT NULL DEFAULT 1,
                auth_token_version INTEGER NOT NULL DEFAULT 0,
                plan TEXT NOT NULL DEFAULT 'free',
                plan_currency TEXT NOT NULL DEFAULT 'PKR',
                plan_activated_at TIMESTAMP,
                plan_expires_at TIMESTAMP,
                billing_country TEXT,
                lifetime_sop_count INTEGER NOT NULL DEFAULT 0,
                air_uni_uni TEXT,
                air_uni_dept TEXT,
                air_uni_batch INTEGER,
                redeemed_invite_code TEXT,
                data_consent_version TEXT,
                data_consent_granted_at TIMESTAMP,
                data_consent_ip TEXT,
                data_consent_user_agent TEXT,
                marketing_consent INTEGER NOT NULL DEFAULT 0,
                b2b_share_consent INTEGER NOT NULL DEFAULT 0,
                b2b_share_consent_at TIMESTAMP,
                gdpr_erasure_requested_at TIMESTAMP,
                account_deleted_at TIMESTAMP,
                parent_consent_email TEXT,
                parent_consent_at TIMESTAMP,
                date_of_birth DATE,
                email_verified_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session
