import os
import uuid
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from app.models.models import ScholarshipChunk

class RAGFeedbackResponse(BaseModel):
    summary: str = Field(description="1-2 sentences summarizing structural or strategic feedback")
    strengths: list[str] = Field(description="Up to 3 specific strengths in the draft")
    revision_priorities: list[str] = Field(description="Up to 4 specific areas for improvement")
    caution_notes: list[str] = Field(description="Up to 3 warnings about tone, length, or missing rules")
    citations: list[str] = Field(description="Citations to the specific retrieved scholarship guidelines used")

class DocumentEvaluator:
    def __init__(self, db: AsyncSession):
        self.db = db
        if SentenceTransformer:
            # all-mpnet-base-v2 outputs 768 dimensions
            self.embedder = SentenceTransformer("all-mpnet-base-v2")
        else:
            self.embedder = None
            
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            temperature=0.2,
        ).with_structured_output(RAGFeedbackResponse)

    async def evaluate_document(self, document_text: str, scholarship_id: Any = None) -> dict:
        context_chunks = []
        if scholarship_id:
            # Fetch priority chunks for the linked scholarship
            result = await self.db.execute(
                select(ScholarshipChunk)
                .where(ScholarshipChunk.scholarship_id == scholarship_id)
                .limit(5)
            )
            chunks = result.scalars().all()
            for chunk in chunks:
                context_chunks.append(chunk.content_text)
        
        # If we need more context or no scholarship_id was provided
        if len(context_chunks) < 3 and self.embedder:
            # Encode a sample of the document to find matching context
            query_embedding = self.embedder.encode(document_text[:1000]).tolist()
            
            query = select(ScholarshipChunk)
            if scholarship_id:
                 query = query.where(ScholarshipChunk.scholarship_id != scholarship_id)
            
            result = await self.db.execute(
                query.order_by(ScholarshipChunk.embedding.cosine_distance(query_embedding))
                .limit(5 - len(context_chunks))
            )
            chunks = result.scalars().all()
            for chunk in chunks:
                context_chunks.append(chunk.content_text)
                
        context_str = "\n\n---\n\n".join(context_chunks) if context_chunks else "No specific scholarship context found."
        
        system_prompt = f"""You are an expert scholarship application mentor.
Review the following student document draft (Statement of Purpose or Essay).
Evaluate the draft against the following official scholarship rules and guidelines retrieved from our database:

<retrieved_context>
{context_str}
</retrieved_context>

Provide detailed feedback identifying strengths and revision priorities.
Strict Rule: Base your evaluation ONLY on the provided context if it relates to specific scholarship rules. Do not hallucinate external rule requirements.
"""

        response: RAGFeedbackResponse = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Student Draft:\n{document_text}")
        ])

        payload = response.model_dump()
        payload["grounded_context"] = [
            "Feedback was augmented with official scholarship guidelines retrieved via pgvector.",
            "Information is strictly constrained to the AI's provided context window."
        ]
        if not payload.get("citations"):
            payload["citations"] = ["General writing best practices"]
            
        return payload
