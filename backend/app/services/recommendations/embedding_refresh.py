from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import RecordState, Scholarship
from app.models.models import ScholarshipChunk
try:
    from app.services.recommendations.hybrid_retriever import OpenSearchHybridRetriever
except Exception:  # pragma: no cover - optional dependency chain
    OpenSearchHybridRetriever = None

logger = logging.getLogger(__name__)

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except Exception:  # pragma: no cover - optional dependency
    RecursiveCharacterTextSplitter = None


_UNSET = object()
_DEFERRED_SOURCE_TOKENS = ("daad",)


class PublishedScholarshipEmbeddingRefresher:
    def __init__(
        self,
        db: AsyncSession,
        *,
        text_splitter: Any = _UNSET,
        embedder: Any = _UNSET,
        retriever: Any = _UNSET,
    ) -> None:
        self.db = db
        self.text_splitter = (
            self._build_text_splitter() if text_splitter is _UNSET else text_splitter
        )
        self.embedder = self._build_embedder() if embedder is _UNSET else embedder
        self.retriever = self._build_retriever() if retriever is _UNSET else retriever

    async def refresh_published_scholarships(
        self,
        *,
        limit: int | None = None,
    ) -> dict[str, int | bool]:
        summary: dict[str, int | bool] = {
            "processed": 0,
            "refreshed": 0,
            "failed": 0,
            "deferred_daad": 0,
            "skipped_missing_text": 0,
            "total_chunks": 0,
            "embedded_chunks": 0,
            "chunked_without_embeddings": 0,
            "indexed": 0,
            "index_failures": 0,
            "model_available": self.embedder is not None,
            "splitter_available": self.text_splitter is not None,
            "retriever_available": self.retriever is not None,
        }

        await self._prepare_index(summary)

        scholarships = await self._load_published_scholarships(limit=limit)
        for scholarship in scholarships:
            if self._is_deferred_source(scholarship):
                summary["deferred_daad"] += 1
                continue

            document_text = self._build_document_text(scholarship)
            if not document_text:
                summary["skipped_missing_text"] += 1
                continue

            summary["processed"] += 1
            try:
                await self._replace_chunks(
                    scholarship=scholarship,
                    document_text=document_text,
                    summary=summary,
                )
                await self.db.commit()
                summary["refreshed"] += 1
            except Exception:
                await self.db.rollback()
                summary["failed"] += 1
                logger.exception(
                    "Embedding refresh failed for scholarship %s",
                    getattr(scholarship, "id", "unknown"),
                )

        return summary

    async def _prepare_index(self, summary: dict[str, int | bool]) -> None:
        if self.retriever is None or self.embedder is None:
            summary["retriever_available"] = False
            return

        try:
            await self.retriever.create_index_if_not_exists()
        except Exception:
            logger.warning(
                "OpenSearch index setup unavailable; continuing without index refresh.",
                exc_info=True,
            )
            self.retriever = None
            summary["retriever_available"] = False

    async def _load_published_scholarships(
        self,
        *,
        limit: int | None,
    ) -> list[Scholarship]:
        statement = (
            select(Scholarship)
            .options(selectinload(Scholarship.source_registry))
            .where(Scholarship.record_state == RecordState.PUBLISHED)
            .order_by(
                Scholarship.published_at.asc().nulls_last(),
                Scholarship.updated_at.desc(),
                Scholarship.title.asc(),
            )
        )
        if limit is not None:
            statement = statement.limit(limit)

        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def _replace_chunks(
        self,
        *,
        scholarship: Scholarship,
        document_text: str,
        summary: dict[str, int | bool],
    ) -> None:
        await self.db.execute(
            delete(ScholarshipChunk).where(
                ScholarshipChunk.scholarship_id == scholarship.id
            )
        )

        chunk_texts = self._split_document(document_text)
        for index, chunk_text in enumerate(chunk_texts):
            chunk_embedding = self._encode_text(chunk_text)
            if chunk_embedding is None:
                summary["chunked_without_embeddings"] += 1
            else:
                summary["embedded_chunks"] += 1

            self.db.add(
                ScholarshipChunk(
                    scholarship_id=scholarship.id,
                    chunk_index=index,
                    content_text=chunk_text,
                    embedding=chunk_embedding,
                )
            )
            summary["total_chunks"] += 1

        await self.db.flush()

        scholarship_embedding = self._encode_text(document_text)
        scholarship.description_embedding = scholarship_embedding
        if scholarship_embedding is None or self.retriever is None:
            return

        try:
            await self.retriever.index_scholarship(scholarship, scholarship_embedding)
            summary["indexed"] += 1
        except Exception:
            summary["index_failures"] += 1
            logger.warning(
                "OpenSearch scholarship index refresh failed for %s",
                scholarship.id,
                exc_info=True,
            )

    def _build_text_splitter(self) -> Any | None:
        if RecursiveCharacterTextSplitter is None:
            return None

        return RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=250,
            length_function=len,
        )

    def _build_embedder(self) -> Any | None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            logger.warning(
                "sentence-transformers is unavailable; scholarship refresh will store text-only chunks.",
                exc_info=True,
            )
            return None

        try:
            return SentenceTransformer("all-mpnet-base-v2")
        except Exception:
            logger.warning(
                "Embedding model could not be initialized; scholarship refresh will store text-only chunks.",
                exc_info=True,
            )
            return None

    def _build_retriever(self) -> Any | None:
        if self.embedder is None or OpenSearchHybridRetriever is None:
            return None

        try:
            return OpenSearchHybridRetriever()
        except Exception:
            logger.warning(
                "OpenSearch retriever unavailable; scholarship refresh will skip index sync.",
                exc_info=True,
            )
            return None

    def _split_document(self, document_text: str) -> list[str]:
        if self.text_splitter is None:
            return [document_text]

        chunks = [chunk.strip() for chunk in self.text_splitter.split_text(document_text)]
        return [chunk for chunk in chunks if chunk] or [document_text]

    def _encode_text(self, text: str) -> list[float] | None:
        if self.embedder is None:
            return None

        try:
            encoded = self.embedder.encode(text)
        except Exception:
            logger.warning("Embedding generation failed for scholarship chunk.", exc_info=True)
            return None

        if hasattr(encoded, "tolist"):
            encoded = encoded.tolist()

        return list(encoded)

    def _build_document_text(self, scholarship: Scholarship) -> str:
        text_parts = [
            f"Title: {scholarship.title}",
            f"Provider: {scholarship.provider_name or 'Unknown'}",
            f"Country: {scholarship.country_code}",
        ]

        if scholarship.summary:
            text_parts.append(f"Summary: {scholarship.summary}")
        if scholarship.funding_summary:
            text_parts.append(f"Funding: {scholarship.funding_summary}")
        if scholarship.field_tags:
            text_parts.append(f"Fields: {', '.join(scholarship.field_tags)}")
        if scholarship.degree_levels:
            text_parts.append(f"Degrees: {', '.join(scholarship.degree_levels)}")
        if scholarship.source_url:
            text_parts.append(f"Source: {scholarship.source_url}")

        return "\n\n".join(part.strip() for part in text_parts if part and part.strip())

    def _is_deferred_source(self, scholarship: Scholarship) -> bool:
        source_registry = getattr(scholarship, "source_registry", None)
        candidate_values = [
            getattr(source_registry, "source_key", None),
            getattr(source_registry, "display_name", None),
            getattr(source_registry, "base_url", None),
            getattr(scholarship, "provider_name", None),
            getattr(scholarship, "source_url", None),
        ]
        normalized_values = [
            str(value).strip().lower()
            for value in candidate_values
            if value is not None and str(value).strip()
        ]
        return any(
            token in value
            for token in _DEFERRED_SOURCE_TOKENS
            for value in normalized_values
        )
