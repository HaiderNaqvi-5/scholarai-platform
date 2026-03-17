import uuid
from datetime import datetime, timezone
from pathlib import Path

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
    DocumentRecordSummary,
    DocumentSubmissionValidation,
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
    ) -> DocumentDetailResponse:
        validation = DocumentSubmissionValidation(
            title=title,
            document_type=document_type,
            content_text=content_text,
            has_file=upload is not None,
        )

        parsed_type = self._parse_document_type(validation.document_type)

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
        )
        self.db.add(document)
        await self.db.flush()

        try:
            document.processing_status = DocumentProcessingStatus.PROCESSING
            payload = await self._generate_feedback_payload(document)
            completed_at = datetime.now(timezone.utc)
            feedback = DocumentFeedback(
                document_id=document.id,
                status=DocumentProcessingStatus.COMPLETED,
                feedback_payload=payload,
                limitation_notice=(
                    "This feedback is generated from your document text and a bounded writing checklist. "
                    "Official scholarship rules still come from validated scholarship records."
                ),
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
        document.processing_status = DocumentProcessingStatus.PROCESSING
        payload = await self._generate_feedback_payload(document)
        completed_at = datetime.now(timezone.utc)
        feedback = DocumentFeedback(
            document_id=document.id,
            status=DocumentProcessingStatus.COMPLETED,
            feedback_payload=payload,
            limitation_notice=(
                "This feedback is generated from your document text and a bounded writing checklist. "
                "Official scholarship rules still come from validated scholarship records."
            ),
            completed_at=completed_at,
        )
        self.db.add(feedback)
        document.processing_status = DocumentProcessingStatus.COMPLETED
        document.latest_feedback_at = completed_at
        await self.db.flush()
        await self.db.refresh(document)
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

    async def _generate_feedback_payload(self, document: DocumentRecord) -> dict:
        text = document.content_text.strip()
        
        try:
            import os
            if os.environ.get("GOOGLE_API_KEY"):
                from app.services.documents.retriever import DocumentEvaluator
                evaluator = DocumentEvaluator(self.db)
                return await evaluator.evaluate_document(text)
        except Exception as e:
            print(f"RAG Evaluation failed, falling back to rules: {e}")

        # Fallback to rules-based processing
        word_count = len(text.split())
        paragraphs = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
        lower_text = text.lower()

        strengths: list[str] = []
        revisions: list[str] = []
        cautions: list[str] = []
        citations: list[str] = []

        if word_count >= 450:
            strengths.append("The draft has enough length to support a clear personal narrative.")
        else:
            revisions.append("Add more concrete evidence about your goals, preparation, and intended impact.")

        if len(paragraphs) >= 3:
            strengths.append("The structure already separates your opening, evidence, and closing sections.")
            citations.extend(["Opening section", "Body section"])
        else:
            revisions.append("Break the draft into clearer sections so motivation, evidence, and future goals do not blur together.")

        if any(keyword in lower_text for keyword in ("research", "project", "thesis", "capstone")):
            strengths.append("You reference concrete academic work, which helps credibility.")
        else:
            revisions.append("Add one or two specific academic or professional examples to ground your claims.")

        if any(keyword in lower_text for keyword in ("community", "impact", "contribute", "goal")):
            strengths.append("The draft hints at future impact, which is useful for scholarship positioning.")
        else:
            revisions.append("State the impact you want to create after the degree more explicitly.")

        if document.document_type == DocumentType.SOP and "scholarship" not in lower_text:
            cautions.append("The draft does not yet mention how it should be tailored for a scholarship or program context.")
        if "gpa" in lower_text or "ielts" in lower_text or "toefl" in lower_text:
            cautions.append("Avoid treating self-reported eligibility facts in the essay as authoritative. The application workflow should verify them separately.")

        summary = (
            "The draft has a usable foundation and should next be tightened around motivation, evidence, and future impact."
            if strengths
            else "The draft needs more structure and evidence before detailed refinement will be useful."
        )

        grounded_context = [
            "Feedback was generated from the submitted document text only.",
            "No raw scholarship pages or policy text were used as authority in this response.",
            "Validated scholarship facts must be injected separately when scholarship-specific tailoring is added later.",
        ]

        if not citations:
            citations.append("Full document draft")

        return {
            "summary": summary,
            "strengths": strengths[:3],
            "revision_priorities": revisions[:4]
            or ["Clarify why this program and scholarship fit your academic direction."],
            "caution_notes": cautions
            or ["Treat this as writing guidance, not official scholarship-rule advice."],
            "citations": citations[:3],
            "grounded_context": grounded_context,
        }

    def _build_summary(self, document: DocumentRecord) -> DocumentRecordSummary:
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
        )

    def _build_detail(self, document: DocumentRecord) -> DocumentDetailResponse:
        latest_feedback = None
        if document.feedback_entries:
            sorted_feedback = sorted(
                document.feedback_entries,
                key=lambda entry: entry.created_at or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
            latest_feedback = self._build_feedback(sorted_feedback[0])

        return DocumentDetailResponse(
            **self._build_summary(document).model_dump(),
            content_text=document.content_text,
            latest_feedback=latest_feedback,
        )

    def _build_feedback(self, feedback: DocumentFeedback) -> DocumentFeedbackResponse:
        payload = feedback.feedback_payload or {}
        return DocumentFeedbackResponse(
            id=str(feedback.id),
            status=feedback.status.value,
            summary=payload.get("summary", "Feedback completed."),
            strengths=list(payload.get("strengths", [])),
            revision_priorities=list(payload.get("revision_priorities", [])),
            caution_notes=list(payload.get("caution_notes", [])),
            citations=list(payload.get("citations", [])),
            grounded_context=list(payload.get("grounded_context", [])),
            limitation_notice=feedback.limitation_notice,
            completed_at=feedback.completed_at,
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
