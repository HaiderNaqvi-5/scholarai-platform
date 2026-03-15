import re
from collections.abc import Iterable

from app.schemas.interviews import InterviewAnswerFeedback, InterviewRubricDimension

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "with",
    "you",
    "your",
}
HEDGING_TERMS = {"maybe", "probably", "perhaps", "kind of", "sort of", "i guess"}
EVIDENCE_TERMS = {
    "built",
    "capstone",
    "delivered",
    "designed",
    "internship",
    "led",
    "measured",
    "project",
    "research",
    "shipped",
    "volunteer",
}
CONFIDENCE_TERMS = {"i led", "i built", "i learned", "i will", "i can", "i am ready"}


class InterviewScoringService:
    scoring_mode = "rules_fallback"

    def score_answer(
        self,
        question_index: int,
        question_text: str,
        answer_text: str,
    ) -> InterviewAnswerFeedback:
        normalized_answer = answer_text.strip()
        tokens = self._tokenize(normalized_answer)
        question_tokens = self._question_keywords(question_text)
        word_count = len(tokens)
        sentence_count = len([part for part in re.split(r"[.!?]+", normalized_answer) if part.strip()])
        lower_answer = normalized_answer.lower()

        clarity_score = self._score_clarity(word_count, sentence_count)
        relevance_score = self._score_relevance(question_tokens, tokens)
        confidence_score = self._score_confidence(lower_answer)
        specificity_score = self._score_specificity(tokens, lower_answer)

        dimensions = [
            self._dimension(
                "clarity",
                clarity_score,
                "The answer is easier to follow when it stays structured and long enough to develop one clear point.",
            ),
            self._dimension(
                "relevance",
                relevance_score,
                "The answer is stronger when it responds directly to the actual question instead of drifting into generic background.",
            ),
            self._dimension(
                "confidence",
                confidence_score,
                "The answer sounds more convincing when it uses direct ownership language rather than hedging.",
            ),
            self._dimension(
                "specificity",
                specificity_score,
                "Interview answers improve when they include concrete evidence, actions, and outcomes.",
            ),
        ]

        overall_score = round(sum(item.score for item in dimensions) / len(dimensions), 2)
        overall_band = self._band(overall_score)
        strengths = self._strengths(dimensions)
        improvement_prompts = self._improvements(dimensions, question_text)

        summary_feedback = (
            "This answer has a usable structure and should next become more specific and scholarship-oriented."
            if overall_score >= 2.75
            else "This answer needs more direct relevance and stronger evidence before it will feel convincing."
        )

        return InterviewAnswerFeedback(
            question_index=question_index,
            question_text=question_text,
            answer_text=normalized_answer,
            overall_score=overall_score,
            overall_band=overall_band,
            scoring_mode=self.scoring_mode,
            summary_feedback=summary_feedback,
            strengths=strengths,
            improvement_prompts=improvement_prompts,
            dimensions=dimensions,
            limitation_notice=(
                "This is a rules-based practice score for coaching only. It is not a prediction of real interview outcomes."
            ),
        )

    def _score_clarity(self, word_count: int, sentence_count: int) -> int:
        if word_count < 45 or sentence_count < 2:
            return 1
        if word_count < 80:
            return 2
        if word_count <= 220 and sentence_count >= 3:
            return 4
        return 3

    def _score_relevance(self, question_tokens: set[str], answer_tokens: list[str]) -> int:
        if not question_tokens:
            return 3
        overlap = len(question_tokens & set(answer_tokens))
        if overlap == 0:
            return 1
        if overlap == 1:
            return 2
        if overlap == 2:
            return 3
        return 4

    def _score_confidence(self, lower_answer: str) -> int:
        confidence_hits = sum(1 for phrase in CONFIDENCE_TERMS if phrase in lower_answer)
        hedging_hits = sum(1 for phrase in HEDGING_TERMS if phrase in lower_answer)
        if confidence_hits >= 2 and hedging_hits == 0:
            return 4
        if confidence_hits >= 1 and hedging_hits <= 1:
            return 3
        if hedging_hits >= 2:
            return 1
        return 2

    def _score_specificity(self, tokens: list[str], lower_answer: str) -> int:
        evidence_hits = len(EVIDENCE_TERMS & set(tokens))
        has_number = any(char.isdigit() for char in lower_answer)
        if evidence_hits >= 3 or (evidence_hits >= 2 and has_number):
            return 4
        if evidence_hits >= 2 or has_number:
            return 3
        if evidence_hits >= 1:
            return 2
        return 1

    def _dimension(self, name: str, score: int, rationale: str) -> InterviewRubricDimension:
        return InterviewRubricDimension(
            dimension=name,
            score=score,
            band=self._band(score),
            rationale=rationale,
        )

    def _strengths(self, dimensions: Iterable[InterviewRubricDimension]) -> list[str]:
        strengths: list[str] = []
        for item in dimensions:
            if item.score >= 3:
                strengths.append(f"{item.dimension.title()} is already a relative strength in this response.")
        return strengths[:3] or ["The answer provides enough material to coach, which is a useful starting point."]

    def _improvements(
        self,
        dimensions: Iterable[InterviewRubricDimension],
        question_text: str,
    ) -> list[str]:
        improvements: list[str] = []
        for item in dimensions:
            if item.score <= 2:
                if item.dimension == "clarity":
                    improvements.append("Rebuild the answer into a simple opening, evidence, and closing structure.")
                elif item.dimension == "relevance":
                    improvements.append(f"Answer the question more directly: {question_text}")
                elif item.dimension == "confidence":
                    improvements.append("Replace hedging language with direct statements about what you did and learned.")
                elif item.dimension == "specificity":
                    improvements.append("Add one concrete example with an action and outcome.")
        return improvements[:3] or ["Tighten the answer so the strongest example appears earlier."]

    def _question_keywords(self, question_text: str) -> set[str]:
        return {
            token
            for token in self._tokenize(question_text)
            if token not in STOPWORDS and len(token) > 3
        }

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-zA-Z']+", text.lower())

    def _band(self, score: float) -> str:
        if score >= 3.5:
            return "strong"
        if score >= 2.5:
            return "solid"
        if score >= 1.5:
            return "developing"
        return "early"
