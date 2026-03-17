import json
import base64
from app.schemas.interviews import InterviewAnswerFeedback, InterviewRubricDimension
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

class GeminiDimension(BaseModel):
    dimension: str = Field(description="Name of the dimension (e.g. clarity, relevance, confidence, specificity)")
    score: int = Field(description="Score from 1 to 4")
    rationale: str = Field(description="One sentence rationale for the score")

class GeminiEvaluation(BaseModel):
    answer_text: str = Field(description="The transcribed text of the user's answer")
    overall_score: float = Field(description="Average score across all dimensions (1.0 to 4.0)")
    summary_feedback: str = Field(description="A brief 1-2 sentence overall summary of the performance")
    strengths: list[str] = Field(description="1 to 3 bullet points highlighting what was done well")
    improvement_prompts: list[str] = Field(description="1 to 3 actionable tips for improvement")
    dimensions: list[GeminiDimension] = Field(description="Detailed scoring for clarity, relevance, confidence, and specificity")

class InterviewEvaluator:
    def __init__(self):
        # We use gemini-2.0-flash which supports audio native multimodal inputs
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            temperature=0.2,
        ).with_structured_output(GeminiEvaluation)

    def _band(self, score: float) -> str:
        if score >= 3.5:
            return "strong"
        if score >= 2.5:
            return "solid"
        if score >= 1.5:
            return "developing"
        return "early"

    def evaluate(self, question_index: int, question_text: str, audio_b64: str = None, text_answer: str = None) -> InterviewAnswerFeedback:
        system_instructions = """You are an expert scholarship interview coach evaluating a student's answer. 
You will be provided with the interview question and the student's response (either as text or an audio file).
Your task is to transcribe the audio (if provided) and evaluate the answer based on four dimensions:
1. Clarity (1-4): Is the answer structured and easy to follow?
2. Relevance (1-4): Does the answer directly address the question?
3. Confidence (1-4): Does the speaker use decisive, ownership language rather than hedging?
4. Specificity (1-4): Are there concrete examples, actions, and outcomes?

Provide constructive, encouraging feedback tailored to a student applying for a prestigious scholarship."""

        content = [
            {"type": "text", "text": f"Question: {question_text}\n\n"}
        ]
        
        if audio_b64:
            # Add audio to multimodal prompt
            # Expecting base64 encoded audio string
            content.append({
                "type": "media",
                "mime_type": "audio/mp3", # Or webm depending on frontend
                "data": audio_b64
            })
        elif text_answer:
            content.append({
                "type": "text",
                "text": f"Student Answer: {text_answer}"
            })
        else:
            raise ValueError("Must provide either audio_b64 or text_answer")

        response: GeminiEvaluation = self.llm.invoke([
            SystemMessage(content=system_instructions),
            HumanMessage(content=content)
        ])

        # Convert to our actual schema
        dimensions = [
            InterviewRubricDimension(
                dimension=d.dimension,
                score=d.score,
                band=self._band(d.score),
                rationale=d.rationale
            ) for d in response.dimensions
        ]

        return InterviewAnswerFeedback(
            question_index=question_index,
            question_text=question_text,
            answer_text=response.answer_text,
            overall_score=response.overall_score,
            overall_band=self._band(response.overall_score),
            scoring_mode="gemini-2.0",
            summary_feedback=response.summary_feedback,
            strengths=response.strengths,
            improvement_prompts=response.improvement_prompts,
            dimensions=dimensions,
            limitation_notice="Evaluated using Gemini AI. This is practice guidance only."
        )
