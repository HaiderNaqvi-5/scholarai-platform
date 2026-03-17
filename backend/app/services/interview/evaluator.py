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

Special Instruction for Audio:
If audio is provided, also evaluate the student's delivery:
- Tone: Is it formal yet passionate?
- Pace: Is it steady or does it show signs of anxiety (rushing/stuttering)?
- Clarity of Speech: Are the words enunciated clearly?

Provide constructive, encouraging feedback tailored to a student applying for a prestigious scholarship. Include a 'Transcription' section at the start of your feedback summary if audio was the primary input."""

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

    async def generate_questions(self, scholarship_context: str, count: int = 3) -> list[str]:
        """
        Generates interview questions tailored to the scholarship guidelines.
        """
        prompt = f"""You are an elite scholarship interviewer.
Based on the following scholarship details, generate {count} challenging but fair interview questions.
Focus on areas where the scholarship has specific values or requirements.

<scholarship_details>
{scholarship_context}
</scholarship_details>

Return ONLY a JSON list of strings."""
        
        # We can use a simpler call here or structured output
        try:
            raw_response = await self.llm.ainvoke([
                SystemMessage(content="Return a JSON list of interview question strings."),
                HumanMessage(content=prompt)
            ])
            # If our LLM is configured with structured output, it might already return a dict/model.
            # But generate_questions is a new use case. Let's assume we can get a list.
            if hasattr(raw_response, "content"):
                 # Parsing if it returns a standard message
                 import re
                 content = raw_response.content
                 match = re.search(r"\[.*\]", content, re.DOTALL)
                 if match:
                      return json.loads(match.group(0))
            return ["Tell us why you are a fit for this specific scholarship.", "How will this scholarship help you achieve your goals?", "Describe a challenge you've overcome that aligns with our values."]
        except Exception as e:
            print(f"Question generation failed: {e}")
            return ["Tell us why you are a fit for this specific scholarship.", "How will this scholarship help you achieve your goals?", "Describe a challenge you've overcome that aligns with our values."]
    async def generate_follow_up(self, question: str, answer: str, context: str = "") -> str:
        """
        Generates a follow-up probing question based on the previous answer.
        """
        prompt = f"""You are a scholarship interviewer. The student just answered a question. 
Generate a short, incisive follow-up question that probes deeper into their specific answer, asking for more detail or challenging a specific claim.

<context>
{context}
</context>

<previous_question>
{question}
</previous_question>

<student_answer>
{answer}
</student_answer>

Return ONLY the follow-up question text."""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a follow-up question generator. Be concise."),
                HumanMessage(content=prompt)
            ])
            if hasattr(response, "content"):
                return response.content.strip()
            return "Could you elaborate more on how that experience shaped your future goals?"
        except Exception:
            return "Could you elaborate more on the specific outcome of that project?"
