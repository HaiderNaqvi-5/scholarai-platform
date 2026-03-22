import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    DocumentFeedback,
    DocumentInputMethod,
    DocumentProcessingStatus,
    DocumentRecord,
    DocumentType,
)
from app.schemas.documents import (
    DocumentDetailResponse,
    DocumentFeedbackResponse,
    DocumentGroundedContextSections,
    DocumentQualityGate,
    DocumentQualityMetrics,
    DocumentRecordSummary,
    DocumentSubmissionValidation,
)
from app.services.documents.grounding import (
    build_scholarship_context_summary,
    build_validated_facts,
    flatten_grounded_context_sections,
    retrieve_bounded_writing_guidance,
    validate_scholarship_grounding,
)
from app.services.kpi_policy import (
    get_document_quality_policy_version,
    get_document_quality_thresholds,
)

MAX_FILE_SIZE_BYTES = 512 * 1024
MAX_TEXT_LENGTH = 12000
ALLOWED_EXTENSIONS = {".txt", ".md"}
RUNTIME_STORAGE_ROOT = Path(__file__).resolve().parents[3] / "runtime" / "documents"
class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_documents(self, user_id: uuid.UUID) -> list[DocumentRecordSummary]:
        result = await self.db.execute(
            select(DocumentRecord)
            .where(DocumentRecord.user_id == user_id)
            .options(selectinload(DocumentRecord.feedback_entries))
            .order_by(DocumentRecord.created_at.desc())
        )
        documents = result.scalars().all()
        return [self._build_summary(document) for document in documents]

    async def get_document(
        self,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> DocumentDetailResponse:
        document = await self._load_document(user_id, document_id)
        return self._build_detail(document)

    async def submit_document(
        self,
        user_id: uuid.UUID,
        document_type: str,
        title: str | None,
        content_text: str | None = None,
        upload: UploadFile | None = None,
        scholarship_id: str | uuid.UUID | None = None,
        scholarship_ids: list[str] | None = None,
    ) -> DocumentDetailResponse:
        validation = DocumentSubmissionValidation(
            title=title,
            document_type=document_type,
            content_text=content_text,
            scholarship_id=str(scholarship_id) if scholarship_id else None,
            scholarship_ids=list(scholarship_ids or []),
            has_file=upload is not None,
        )

        parsed_type = self._parse_document_type(validation.document_type)
        grounded_scholarships = await validate_scholarship_grounding(
            self.db,
            scholarship_id=validation.scholarship_id,
            scholarship_ids=validation.scholarship_ids,
        )

        if upload is not None:
            input_method = DocumentInputMethod.FILE
            document_text, storage_path, original_filename, mime_type, file_size = (
                await self._store_uploaded_file(user_id, upload)
            )
            effective_title = title or Path(original_filename).stem or "Uploaded document"
        else:
            input_method = DocumentInputMethod.TEXT
            document_text = (content_text or "").strip()
            storage_path = None
            original_filename = None
            mime_type = None
            file_size = len(document_text.encode("utf-8"))
            effective_title = title or self._default_title(parsed_type)

        persisted_scholarship_id = grounded_scholarships[0].id if grounded_scholarships else None
        document = DocumentRecord(
            user_id=user_id,
            title=effective_title,
            document_type=parsed_type,
            input_method=input_method,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size_bytes=file_size,
            storage_path=storage_path,
            content_text=document_text,
            processing_status=DocumentProcessingStatus.SUBMITTED,
            scholarship_id=persisted_scholarship_id,
        )
        self.db.add(document)
        await self.db.flush()

        try:
            document.processing_status = DocumentProcessingStatus.PROCESSING
            payload = await self._generate_feedback_payload(document, grounded_scholarships)
            completed_at = datetime.now(timezone.utc)
            feedback = DocumentFeedback(
                document_id=document.id,
                status=DocumentProcessingStatus.COMPLETED,
                feedback_payload=payload,
                limitation_notice=self._limitation_notice(grounded_scholarships),
                completed_at=completed_at,
            )
            self.db.add(feedback)
            document.processing_status = DocumentProcessingStatus.COMPLETED
            document.latest_feedback_at = completed_at
            await self.db.flush()
            await self.db.refresh(document)
        except HTTPException:
            document.processing_status = DocumentProcessingStatus.FAILED
            await self.db.flush()
            raise
        except Exception as exc:
            document.processing_status = DocumentProcessingStatus.FAILED
            await self.db.flush()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The document feedback pipeline failed unexpectedly",
            ) from exc

        document = await self._load_document(user_id, document.id)
        return self._build_detail(document)

    async def regenerate_feedback(
        self,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> DocumentDetailResponse:
        document = await self._load_document(user_id, document_id)
        grounded_scholarships = await self._resolve_grounded_scholarships(document)
        document.processing_status = DocumentProcessingStatus.PROCESSING

        try:
            payload = await self._generate_feedback_payload(document, grounded_scholarships)
            completed_at = datetime.now(timezone.utc)
            feedback = DocumentFeedback(
                document_id=document.id,
                status=DocumentProcessingStatus.COMPLETED,
                feedback_payload=payload,
                limitation_notice=self._limitation_notice(grounded_scholarships),
                completed_at=completed_at,
            )
            self.db.add(feedback)
            document.processing_status = DocumentProcessingStatus.COMPLETED
            document.latest_feedback_at = completed_at
            await self.db.flush()
            await self.db.refresh(document)
        except HTTPException:
            document.processing_status = DocumentProcessingStatus.FAILED
            await self.db.flush()
            raise

        document = await self._load_document(user_id, document.id)
        return self._build_detail(document)

    async def _load_document(
        self,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> DocumentRecord:
        result = await self.db.execute(
            select(DocumentRecord)
            .where(
                DocumentRecord.id == document_id,
                DocumentRecord.user_id == user_id,
            )
            .options(selectinload(DocumentRecord.feedback_entries))
        )
        document = result.scalar_one_or_none()
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        return document

    async def _store_uploaded_file(
        self,
        user_id: uuid.UUID,
        upload: UploadFile,
    ) -> tuple[str, str, str, str | None, int]:
        filename = upload.filename or "document.txt"
        suffix = Path(filename).suffix.lower()
        content_type = upload.content_type or ""
        if suffix not in ALLOWED_EXTENSIONS or (
            content_type and not content_type.startswith("text/")
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only plain-text .txt or .md uploads are supported in the MVP",
            )

        raw_bytes = await upload.read()
        if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file exceeds the 512KB MVP limit",
            )

        try:
            content_text = raw_bytes.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must be UTF-8 encoded plain text",
            ) from exc

        if len(content_text) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document text must contain at least 50 characters",
            )

        if len(content_text) > MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document text exceeds the 12000 character MVP limit",
            )

        user_dir = RUNTIME_STORAGE_ROOT / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        storage_name = f"{uuid.uuid4()}{suffix or '.txt'}"
        storage_path = user_dir / storage_name
        storage_path.write_text(content_text, encoding="utf-8")

        return (
            content_text,
            str(storage_path),
            filename,
            upload.content_type,
            len(raw_bytes),
        )

    async def _generate_feedback_payload(
        self,
        document: DocumentRecord,
        grounded_scholarships: list[Any],
    ) -> dict[str, Any]:
        text = document.content_text.strip()
        word_count = len(text.split())
        paragraphs = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
        lower_text = text.lower()

        strengths: list[str] = []
        revisions: list[str] = []
        cautions: list[str] = []

        if word_count >= 450:
            strengths.append("The draft has enough length to support a clear personal narrative.")
        else:
            revisions.append("Add more concrete evidence about your goals, preparation, and intended impact.")

        if len(paragraphs) >= 3:
            strengths.append("The structure already separates your opening, evidence, and closing sections.")
        else:
            revisions.append(
                "Break the draft into clearer sections so motivation, evidence, and future goals do not blur together."
            )

        if any(keyword in lower_text for keyword in ("research", "project", "thesis", "capstone")):
            strengths.append("You reference concrete academic work, which helps credibility.")
        else:
            revisions.append("Add one or two specific academic or professional examples to ground your claims.")

        if any(keyword in lower_text for keyword in ("community", "impact", "contribute", "goal")):
            strengths.append("The draft hints at future impact, which is useful for scholarship positioning.")
        else:
            revisions.append("State the impact you want to create after the degree more explicitly.")

        if document.document_type == DocumentType.SOP and "scholarship" not in lower_text and grounded_scholarships:
            cautions.append("The draft still needs an explicit bridge between your goals and the grounded scholarship context.")
        if "gpa" in lower_text or "ielts" in lower_text or "toefl" in lower_text:
            cautions.append(
                "Avoid treating self-reported eligibility facts in the essay as authoritative. The application workflow should verify them separately."
            )

        validated_facts = build_validated_facts(grounded_scholarships)
        retrieved_guidance = retrieve_bounded_writing_guidance(
            document.document_type.value,
            grounded_scholarships,
        )
        generated_guidance = self._build_generated_guidance(
            grounded_scholarships,
            validated_facts,
            retrieved_guidance,
            lower_text,
        )

        summary = (
            "The draft has a usable foundation and should next align its evidence more tightly with the validated scholarship context."
            if grounded_scholarships
            else "The draft has a usable foundation and should next be tightened around motivation, evidence, and future impact."
        )

        sections = {
            "validated_facts": validated_facts,
            "retrieved_writing_guidance": retrieved_guidance,
            "generated_guidance": generated_guidance,
            "limitations": self._build_limitations(grounded_scholarships),
        }

        citations = [
            f"{scholarship.title} | {scholarship.source_url}"
            for scholarship in grounded_scholarships
        ] or ["Full document draft"]

        return {
            "summary": summary,
            "strengths": strengths[:3],
            "revision_priorities": revisions[:4]
            or ["Clarify why this program and scholarship fit your academic direction."],
            "caution_notes": cautions
            or ["Treat generated coaching as writing guidance, not as official policy advice."],
            "citations": citations[:4],
            "grounded_context": flatten_grounded_context_sections(sections),
            "grounded_context_sections": sections,
            "grounding": {
                "scholarship_ids": [str(scholarship.id) for scholarship in grounded_scholarships],
                "context_summary": build_scholarship_context_summary(grounded_scholarships),
            },
        }

    async def _resolve_grounded_scholarships(self, document: DocumentRecord) -> list[Any]:
        grounding_ids: list[str] = []
        feedback_entries = self._sorted_feedback_entries(document)
        if feedback_entries:
            latest_payload = feedback_entries[0].feedback_payload or {}
            grounding_ids = list(latest_payload.get("grounding", {}).get("scholarship_ids", []))

        if not grounding_ids and document.scholarship_id:
            grounding_ids = [str(document.scholarship_id)]

        return await validate_scholarship_grounding(self.db, scholarship_ids=grounding_ids)

    def _build_generated_guidance(
        self,
        grounded_scholarships: list[Any],
        validated_facts: list[dict[str, str]],
        retrieved_guidance: list[dict[str, str]],
        lower_text: str,
    ) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []

        for snippet in retrieved_guidance[:2]:
            items.append(
                {
                    "type": "retrieved_guidance_application",
                    "guidance": f"Apply the {snippet['topic'].lower()} guidance directly in one paragraph: {snippet['snippet']}",
                }
            )

        if grounded_scholarships:
            primary = grounded_scholarships[0]
            items.append(
                {
                    "type": "scholarship_fit",
                    "guidance": f"Name why {primary.title} is a fit for your graduate direction instead of describing it as generic funding.",
                }
            )
            if primary.field_tags:
                items.append(
                    {
                        "type": "field_alignment",
                        "guidance": f"Connect your prior work to these validated field areas: {', '.join(primary.field_tags[:3])}.",
                    }
                )
            if primary.category and primary.category.lower() not in lower_text:
                items.append(
                    {
                        "type": "category_alignment",
                        "guidance": f"Make the {primary.category.lower()} emphasis explicit in your examples and future-impact section.",
                    }
                )
        elif not validated_facts:
            items.append(
                {
                    "type": "ungrounded_mode",
                    "guidance": "Because no scholarship grounding was provided, keep the draft broadly scholarship-ready and avoid inventing program-specific claims.",
                }
            )

        return items[:5]

    def _build_summary(self, document: DocumentRecord) -> DocumentRecordSummary:
        scholarship_ids: list[str] | None = None
        feedback_entries = self._sorted_feedback_entries(document)
        if feedback_entries:
            latest_payload = feedback_entries[0].feedback_payload or {}
            grounding_payload = latest_payload.get("grounding", {})
            ids = grounding_payload.get("scholarship_ids")
            if isinstance(ids, list) and ids:
                scholarship_ids = [str(value) for value in ids]

        return DocumentRecordSummary(
            id=str(document.id),
            title=document.title,
            document_type=document.document_type.value,
            input_method=document.input_method.value,
            processing_status=document.processing_status.value,
            original_filename=document.original_filename,
            created_at=document.created_at,
            updated_at=document.updated_at,
            latest_feedback_at=document.latest_feedback_at,
            scholarship_id=str(document.scholarship_id) if document.scholarship_id else None,
            scholarship_ids=scholarship_ids,
        )

    def _build_detail(self, document: DocumentRecord) -> DocumentDetailResponse:
        latest_feedback = None
        feedback_entries = self._sorted_feedback_entries(document)
        if feedback_entries:
            latest_feedback = self._build_feedback(feedback_entries[0])

        return DocumentDetailResponse(
            **self._build_summary(document).model_dump(),
            content_text=document.content_text,
            latest_feedback=latest_feedback,
        )

    def _build_feedback(self, feedback: DocumentFeedback) -> DocumentFeedbackResponse:
        payload = feedback.feedback_payload or {}
        raw_sections = payload.get("grounded_context_sections")
        sections = (
            cast(dict[str, Any], raw_sections)
            if isinstance(raw_sections, dict)
            else self._legacy_grounded_sections(payload)
        )
        sections_model = DocumentGroundedContextSections(**sections)
        return DocumentFeedbackResponse(
            id=str(feedback.id),
            status=feedback.status.value,
            summary=payload.get("summary", "Feedback completed."),
            strengths=list(payload.get("strengths", [])),
            revision_priorities=list(payload.get("revision_priorities", [])),
            caution_notes=list(payload.get("caution_notes", [])),
            citations=list(payload.get("citations", [])),
            grounded_context=list(payload.get("grounded_context", [])),
            validated_facts=sections_model.validated_facts,
            retrieved_writing_guidance=sections_model.retrieved_writing_guidance,
            generated_guidance=sections_model.generated_guidance,
            limitations=sections_model.limitations,
            grounded_context_sections=DocumentGroundedContextSections(
                validated_facts=sections_model.validated_facts,
                retrieved_writing_guidance=sections_model.retrieved_writing_guidance,
                generated_guidance=sections_model.generated_guidance,
                limitations=sections_model.limitations,
            ),
            quality_metrics=self._build_quality_metrics(payload, sections),
            quality_gate=self._build_quality_gate(payload, sections),
            limitation_notice=feedback.limitation_notice,
            completed_at=feedback.completed_at,
        )

    def _build_quality_gate(
        self,
        payload: dict[str, Any],
        sections: dict[str, Any],
    ) -> DocumentQualityGate:
        metrics = self._build_quality_metrics(payload, sections)
        thresholds = get_document_quality_thresholds()

        citation_coverage_pass = (
            metrics.citation_coverage_ratio >= thresholds.min_citation_coverage_ratio
        )
        caution_note_count_pass = (
            metrics.caution_note_count <= thresholds.max_caution_note_count
        )
        retrieved_guidance_pass = (
            metrics.retrieved_guidance_count >= thresholds.min_retrieved_guidance_count
        )
        generated_guidance_pass = (
            metrics.generated_guidance_count >= thresholds.min_generated_guidance_count
        )

        return DocumentQualityGate(
            thresholds=thresholds,
            policy_version=get_document_quality_policy_version(),
            citation_coverage_pass=citation_coverage_pass,
            caution_note_count_pass=caution_note_count_pass,
            retrieved_guidance_pass=retrieved_guidance_pass,
            generated_guidance_pass=generated_guidance_pass,
            all_passed=(
                citation_coverage_pass
                and caution_note_count_pass
                and retrieved_guidance_pass
                and generated_guidance_pass
            ),
        )

    def _build_quality_metrics(
        self,
        payload: dict[str, Any],
        sections: dict[str, Any],
    ) -> DocumentQualityMetrics:
        citations = list(payload.get("citations", []))
        validated_facts = list(sections.get("validated_facts", []))
        retrieved = list(sections.get("retrieved_writing_guidance", []))
        generated = list(sections.get("generated_guidance", []))
        caution_notes = list(payload.get("caution_notes", []))

        citation_coverage_ratio = 1.0 if not validated_facts else min(len(citations) / len(validated_facts), 1.0)
        review_flag = citation_coverage_ratio < 0.8 or len(caution_notes) >= 2

        return DocumentQualityMetrics(
            citation_coverage_ratio=round(citation_coverage_ratio, 4),
            validated_fact_count=len(validated_facts),
            retrieved_guidance_count=len(retrieved),
            generated_guidance_count=len(generated),
            caution_note_count=len(caution_notes),
            review_flag=review_flag,
        )

    def _legacy_grounded_sections(self, payload: dict[str, Any]) -> dict[str, Any]:
        legacy_context = list(payload.get("grounded_context", []))
        return {
            "validated_facts": [],
            "retrieved_writing_guidance": [],
            "generated_guidance": [
                {"type": "legacy_context", "guidance": item} for item in legacy_context
            ],
            "limitations": [
                "This feedback entry predates structured grounded sections and was mapped into the additive response shape."
            ],
        }

    def _sorted_feedback_entries(self, document: DocumentRecord) -> list[DocumentFeedback]:
        return sorted(
            document.feedback_entries,
            key=lambda entry: entry.created_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

    def _parse_document_type(self, value: str) -> DocumentType:
        try:
            return DocumentType(value.lower())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document type must be 'sop' or 'essay'",
            ) from exc

    def _default_title(self, document_type: DocumentType) -> str:
        if document_type == DocumentType.ESSAY:
            return "Essay draft"
        return "Statement of purpose draft"

    def _build_limitations(self, grounded_scholarships: list[Any]) -> list[str]:
        limitations = [
            "Generated guidance is bounded coaching, not an official eligibility determination.",
            "Only validated scholarship record fields were used as scholarship facts.",
        ]
        if grounded_scholarships:
            limitations.append(
                "Retrieved writing guidance comes from a small in-repo guidance set rather than a broad scholarship corpus."
            )
        else:
            limitations.append(
                "No scholarship grounding IDs were provided, so scholarship-specific tailoring stayed intentionally limited."
            )
        return limitations

    def _limitation_notice(self, grounded_scholarships: list[Any]) -> str:
        if grounded_scholarships:
            return (
                "This feedback separates validated scholarship facts from bounded writing guidance and generated coaching. "
                "Official scholarship rules still come from published scholarship records."
            )
        return (
            "This feedback uses bounded writing guidance and generated coaching only. "
            "Official scholarship rules still come from validated scholarship records."
        )
