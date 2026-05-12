"""Data export service (Feature 9.5, PRD §9.5).

Assembles every piece of user-owned data into a JSON + Markdown bundle
and stores it as a temporary file with a 7-day expiry. The Celery
deployment can later push the bundle to S3 with a signed URL; here we
return a local file:// path so unit tests stay deterministic.
"""

from __future__ import annotations

import io
import json
import logging
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ApplicationTrackerItem,
    ConsentAuditLog,
    DataExportRequest,
    DocumentRecord,
    InterviewResponse,
    InterviewSession,
    StudentProfile,
    User,
)


logger = logging.getLogger(__name__)

EXPORT_ROOT = Path(__file__).resolve().parents[3] / "runtime" / "exports"
EXPORT_TTL = timedelta(days=7)


class ExportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def request_export(self, user: User) -> DataExportRequest:
        record = DataExportRequest(user_id=user.id, status="pending")
        self.db.add(record)
        await self.db.flush()
        return record

    async def fulfil_export(self, request_id: uuid.UUID) -> DataExportRequest | None:
        record = await self.db.get(DataExportRequest, request_id)
        if record is None:
            return None
        record.status = "running"
        await self.db.flush()

        user = await self.db.get(User, record.user_id)
        if user is None:
            record.status = "failed"
            await self.db.flush()
            return record

        bundle_bytes = await self._build_bundle(user)
        EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
        filename = f"user-{user.id}-{int(datetime.now(timezone.utc).timestamp())}.zip"
        path = EXPORT_ROOT / filename
        path.write_bytes(bundle_bytes)

        record.status = "completed"
        record.completed_at = datetime.now(timezone.utc)
        record.download_url = path.as_uri()
        record.expires_at = record.completed_at + EXPORT_TTL
        await self.db.flush()
        return record

    async def _build_bundle(self, user: User) -> bytes:
        profile = await self._fetch_profile(user.id)
        tracker = await self._fetch_tracker(user.id)
        documents = await self._fetch_documents(user.id)
        interview_sessions = await self._fetch_interviews(user.id)
        consent = await self._fetch_consent_log(user.id)

        manifest = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user": _serialise_user(user),
            "profile": _serialise_profile(profile),
            "tracker": [_serialise_tracker(t) for t in tracker],
            "documents": [_serialise_document(d) for d in documents],
            "interview_sessions": [_serialise_interview(*pair) for pair in interview_sessions],
            "consent_audit_log": [_serialise_consent(c) for c in consent],
        }

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("user_data.json", json.dumps(manifest, indent=2, default=str))
            archive.writestr("README.md", _render_readme(manifest))
        return buffer.getvalue()

    async def _fetch_profile(self, user_id: uuid.UUID) -> StudentProfile | None:
        result = await self.db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _fetch_tracker(self, user_id: uuid.UUID) -> list[ApplicationTrackerItem]:
        result = await self.db.execute(
            select(ApplicationTrackerItem).where(ApplicationTrackerItem.user_id == user_id)
        )
        return list(result.scalars().all())

    async def _fetch_documents(self, user_id: uuid.UUID) -> list[DocumentRecord]:
        result = await self.db.execute(
            select(DocumentRecord).where(DocumentRecord.user_id == user_id)
        )
        return list(result.scalars().all())

    async def _fetch_interviews(
        self, user_id: uuid.UUID
    ) -> list[tuple[InterviewSession, list[InterviewResponse]]]:
        sessions_result = await self.db.execute(
            select(InterviewSession).where(InterviewSession.user_id == user_id)
        )
        out: list[tuple[InterviewSession, list[InterviewResponse]]] = []
        for session in sessions_result.scalars().all():
            r = await self.db.execute(
                select(InterviewResponse).where(InterviewResponse.session_id == session.id)
            )
            out.append((session, list(r.scalars().all())))
        return out

    async def _fetch_consent_log(self, user_id: uuid.UUID) -> list[ConsentAuditLog]:
        result = await self.db.execute(
            select(ConsentAuditLog)
            .where(ConsentAuditLog.user_id == user_id)
            .order_by(ConsentAuditLog.granted_at.asc())
        )
        return list(result.scalars().all())


def _serialise_user(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value if user.role else None,
        "plan": user.plan,
        "plan_currency": user.plan_currency,
        "billing_country": user.billing_country,
        "marketing_consent": bool(user.marketing_consent),
        "b2b_share_consent": bool(user.b2b_share_consent),
        "account_deleted_at": user.account_deleted_at.isoformat() if user.account_deleted_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _serialise_profile(profile: StudentProfile | None) -> dict | None:
    if profile is None:
        return None
    return {
        "citizenship_country_code": profile.citizenship_country_code,
        "gpa_value": float(profile.gpa_value) if profile.gpa_value is not None else None,
        "gpa_scale": float(profile.gpa_scale) if profile.gpa_scale is not None else None,
        "target_field": profile.target_field,
        "target_degree_level": profile.target_degree_level.value if profile.target_degree_level else None,
        "target_countries": list(profile.target_countries or []),
        "target_fields": list(profile.target_fields or []),
        "ielts_score": float(profile.ielts_score) if profile.ielts_score is not None else None,
        "toefl_score": profile.toefl_score,
        "gre_quant": profile.gre_quant,
        "gre_verbal": profile.gre_verbal,
        "hec_degree_level": profile.hec_degree_level,
        "pakistani_university": profile.pakistani_university,
        "degree_subject": profile.degree_subject,
        "graduation_year": profile.graduation_year,
        "funding_requirement": profile.funding_requirement,
        "intake_target": profile.intake_target,
        "city_of_origin": profile.city_of_origin,
        "lead_score": profile.lead_score,
    }


def _serialise_tracker(item: ApplicationTrackerItem) -> dict:
    return {
        "id": str(item.id),
        "scholarship_id": str(item.scholarship_id) if item.scholarship_id else None,
        "university_id": str(item.university_id) if item.university_id else None,
        "program_name": item.program_name,
        "university_name": item.university_name,
        "country": item.country,
        "stage": item.stage,
        "deadline": item.deadline.isoformat() if item.deadline else None,
        "notes": item.notes,
        "document_checklist": dict(item.document_checklist or {}),
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _serialise_document(doc: DocumentRecord) -> dict:
    return {
        "id": str(doc.id),
        "title": doc.title,
        "document_type": doc.document_type.value if doc.document_type else None,
        "input_method": doc.input_method.value if doc.input_method else None,
        "processing_status": doc.processing_status.value if doc.processing_status else None,
        "content_text": doc.content_text,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def _serialise_interview(session: InterviewSession, responses: list[InterviewResponse]) -> dict:
    return {
        "id": str(session.id),
        "country": session.country,
        "visa_type": session.visa_type,
        "practice_mode": session.practice_mode.value if session.practice_mode else None,
        "status": session.status.value if session.status else None,
        "total_questions": session.total_questions,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "responses": [
            {
                "question_index": r.question_index,
                "question_text": r.question_text,
                "answer_text": r.answer_text,
                "score_payload": dict(r.score_payload or {}),
            }
            for r in responses
        ],
    }


def _serialise_consent(row: ConsentAuditLog) -> dict:
    return {
        "consent_type": row.consent_type,
        "version": row.version,
        "action": row.action,
        "granted_at": row.granted_at.isoformat() if row.granted_at else None,
        "document_sha256": row.document_sha256,
    }


def _render_readme(manifest: dict) -> str:
    return (
        "# Your ScholarAI / GrantPath data export\n\n"
        f"Exported at: {manifest['exported_at']}\n\n"
        "This ZIP contains every piece of data we hold about you, as required by "
        "GDPR Article 20 and equivalent provisions of UK DPA 2018, Pakistani PDPB, "
        "Canadian PIPEDA, and California CCPA. \n\n"
        "Files:\n"
        "- `user_data.json` — machine-readable bundle of profile, tracker, documents,\n"
        "  interview transcripts, and consent history.\n"
        "- `README.md` — this file.\n\n"
        "Need a deletion? POST /api/v1/privacy/account-deletion. We schedule deletion "
        "30 days out so you can cancel. Consent audit logs are retained 7 years for "
        "legal defensibility, with all PII anonymised on the cutover date.\n"
    )
