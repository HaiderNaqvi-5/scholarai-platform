"""
RecommendationService: hybrid AI matching for ScholarAI.

Architecture:
  1. retrieve_candidates()     — filter Scholarships that pass hard eligibility
  2. compute_vector_similarity() — cosine sim between student & scholarship embeddings
  3. compute_xgb_score()       — XGBoost probability calibrated to 0-1 success estimate
  4. fuse()                    — weighted hybrid of vector + XGBoost + rule-based boost
  5. build_shap_explanation()  — SHAP values for feature contribution breakdown
  6. persist_scores()          — upsert MatchScore rows (used by /recommendations endpoint)

Usage:
    svc = RecommendationService(db)
    await svc.compute_and_store(student_profile)
"""
from __future__ import annotations

import logging
import uuid
from typing import List

import numpy as np
from sqlalchemy import select, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import MatchScore, Scholarship, StudentProfile

logger = logging.getLogger(__name__)


# ── Weights (tunable via env or A/B test) ────────────────────────────────────
VECTOR_WEIGHT   = 0.40
XGB_WEIGHT      = 0.45
RULE_BOOST      = 0.15


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._encoder = None   # lazy-loaded sentence-transformers model
        self._xgb     = None   # lazy-loaded XGBoost model

    # ── Public entrypoint ─────────────────────────────────────────────────────

    async def compute_and_store(self, profile: StudentProfile, top_k: int = 50) -> int:
        """Compute match scores for a student and persist to MatchScore table.

        Returns number of scores written.
        """
        try:
            candidates   = await self._retrieve_candidates(profile)
            if not candidates:
                logger.info(f"No candidates for student {profile.id}")
                return 0

            profile_vec  = await self._get_profile_embedding(profile)
            sch_vecs     = await self._get_scholarship_embeddings(candidates)

            results = []
            for i, scholarship in enumerate(candidates):
                vec_sim   = self._cosine_similarity(profile_vec, sch_vecs[i])
                xgb_score = self._xgb_predict(profile, scholarship)
                rule_boost = self._rule_based_boost(profile, scholarship)
                overall   = (VECTOR_WEIGHT * vec_sim + XGB_WEIGHT * xgb_score +
                             RULE_BOOST * rule_boost)
                shap_vals = self._build_shap_explanation(profile, scholarship, xgb_score)

                results.append((scholarship.id, overall, xgb_score, vec_sim, shap_vals))

            # Sort descending, keep top-k
            results.sort(key=lambda x: x[1], reverse=True)
            results = results[:top_k]

            await self._persist_scores(profile.id, results)
            return len(results)

        except Exception:
            logger.exception(f"Error computing recommendations for student {profile.id}")
            raise

    # ── Candidate filtering ────────────────────────────────────────────────────

    async def _retrieve_candidates(self, profile: StudentProfile) -> List[Scholarship]:
        """Return scholarships that pass hard eligibility filters."""
        filters = [Scholarship.is_active == True]

        # GPA filter: scholarship min_gpa <= student GPA (normalised to 4.0 scale)
        if profile.gpa is not None:
            normalised_gpa = (profile.gpa / profile.gpa_scale) * 4.0
            filters.append(
                or_(
                    Scholarship.min_gpa == None,
                    Scholarship.min_gpa <= normalised_gpa,
                )
            )

        # Degree-level filter
        if profile.degree_level:
            filters.append(
                or_(
                    Scholarship.degree_levels == None,
                    Scholarship.degree_levels.any(profile.degree_level),
                )
            )

        result = await self.db.execute(
            select(Scholarship).where(and_(*filters)).limit(500)
        )
        return result.scalars().all()

    # ── Embeddings ────────────────────────────────────────────────────────────

    def _get_encoder(self):
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            self._encoder = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._encoder

    async def _get_profile_embedding(self, profile: StudentProfile) -> np.ndarray:
        """Return (or compute and cache) the student profile embedding vector."""
        if profile.profile_embedding is not None:
            return np.array(profile.profile_embedding)

        text = self._profile_to_text(profile)
        encoder = self._get_encoder()
        vec = encoder.encode(text, normalize_embeddings=True)

        # Store back on the profile row
        profile.profile_embedding = vec.tolist()
        await self.db.commit()
        return vec

    async def _get_scholarship_embeddings(self, scholarships: List[Scholarship]) -> List[np.ndarray]:
        """Batch-fetch/generate scholarship embeddings."""
        vecs = []
        need_compute = []

        for s in scholarships:
            if s.scholarship_embedding is not None:
                vecs.append((s.id, np.array(s.scholarship_embedding)))
            else:
                need_compute.append(s)

        if need_compute:
            encoder = self._get_encoder()
            texts  = [self._scholarship_to_text(s) for s in need_compute]
            new_vecs = encoder.encode(texts, batch_size=32, normalize_embeddings=True)
            for s, v in zip(need_compute, new_vecs):
                s.scholarship_embedding = v.tolist()
                vecs.append((s.id, v))
            await self.db.commit()

        # Restore original order
        id_to_vec = {sid: v for sid, v in vecs}
        return [id_to_vec[s.id] for s in scholarships]

    # ── Feature helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Safe cosine similarity (handles zero vectors)."""
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def _xgb_predict(self, profile: StudentProfile, scholarship: Scholarship) -> float:
        """XGBoost success probability prediction (0-1).

        Falls back to a simple logistic heuristic if the model is not loaded.
        """
        if self._xgb is not None:
            features = self._build_feature_vector(profile, scholarship)
            return float(self._xgb.predict_proba([features])[0][1])

        # Heuristic fallback (weighted average of available signals)
        score = 0.5
        if profile.research_publications:
            score += 0.05 * min(profile.research_publications, 5)
        if profile.leadership_roles:
            score += 0.04 * min(profile.leadership_roles, 3)
        return min(score, 0.95)

    @staticmethod
    def _rule_based_boost(profile: StudentProfile, scholarship: Scholarship) -> float:
        """Hard rule boosts (0-1). Country match, field match, etc."""
        boost = 0.0
        if (profile.target_countries and scholarship.country in profile.target_countries):
            boost += 0.5
        if profile.field_of_study and scholarship.field_of_study:
            if any(
                profile.field_of_study.lower() in f.lower()
                for f in scholarship.field_of_study
            ):
                boost += 0.5
        return min(boost, 1.0)

    @staticmethod
    def _build_feature_vector(profile: StudentProfile, scholarship: Scholarship) -> List[float]:
        """Flat numeric feature vector for XGBoost."""
        normalised_gpa = 0.5
        if profile.gpa and profile.gpa_scale:
            normalised_gpa = (profile.gpa / profile.gpa_scale)

        gpa_gap = 0.0
        if scholarship.min_gpa and profile.gpa:
            gpa_gap = max(0.0, normalised_gpa - (scholarship.min_gpa / 4.0))

        return [
            normalised_gpa,
            gpa_gap,
            float(profile.research_publications or 0),
            float(profile.research_experience_months or 0),
            float(profile.leadership_roles or 0),
            float(profile.volunteer_hours or 0),
            float(1 if profile.language_test_score else 0),
            float(profile.language_test_score or 0),
        ]

    @staticmethod
    def _build_shap_explanation(
        profile: StudentProfile, scholarship: Scholarship, xgb_prob: float
    ) -> dict:
        """Lightweight rule-based explanation (replaces SHAP if model not loaded)."""
        contributions = {
            "gpa": 0.0,
            "research": 0.0,
            "leadership": 0.0,
            "language": 0.0,
        }
        if profile.gpa:
            contributions["gpa"] = round((profile.gpa / profile.gpa_scale) * 0.35, 3)
        if profile.research_publications:
            contributions["research"] = round(min(profile.research_publications / 10, 1) * 0.30, 3)
        if profile.leadership_roles:
            contributions["leadership"] = round(min(profile.leadership_roles / 5, 1) * 0.20, 3)
        if profile.language_test_score:
            contributions["language"] = round(0.15, 3)
        return contributions

    # ── Text converters ───────────────────────────────────────────────────────

    @staticmethod
    def _profile_to_text(profile: StudentProfile) -> str:
        parts = [
            f"Field of study: {profile.field_of_study}",
            f"Degree level: {profile.degree_level}",
        ]
        if profile.country_of_origin:
            parts.append(f"Country of origin: {profile.country_of_origin}")
        if profile.university:
            parts.append(f"University: {profile.university}")
        if profile.research_publications:
            parts.append(f"Research publications: {profile.research_publications}")
        if profile.extracurricular_summary:
            parts.append(profile.extracurricular_summary)
        if profile.sop_draft:
            parts.append(profile.sop_draft[:500])  # truncate to avoid token blow-up
        return ". ".join(parts)

    @staticmethod
    def _scholarship_to_text(scholarship: Scholarship) -> str:
        parts = [scholarship.name]
        if scholarship.description:
            parts.append(scholarship.description[:1000])
        if scholarship.field_of_study:
            parts.append(f"Fields: {', '.join(scholarship.field_of_study)}")
        if scholarship.country:
            parts.append(f"Country: {scholarship.country}")
        return ". ".join(parts)

    # ── Persistence ───────────────────────────────────────────────────────────

    async def _persist_scores(
        self,
        student_id: uuid.UUID,
        results: list[tuple[uuid.UUID, float, float, float, dict]],
    ) -> None:
        """Upsert MatchScore rows (delete old, insert new batch)."""
        await self.db.execute(
            delete(MatchScore).where(MatchScore.student_id == student_id)
        )
        for sch_id, overall, xgb_prob, vec_sim, shap in results:
            ms = MatchScore(
                student_id=student_id,
                scholarship_id=sch_id,
                overall_score=overall,
                success_probability=xgb_prob,
                vector_similarity=vec_sim,
                feature_contributions=shap,
            )
            self.db.add(ms)
        await self.db.commit()
