from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class StartInterviewRequest(BaseModel):
    scholarship_id: Optional[str] = None
    interview_type: str = "general"
    difficulty: str = "intermediate"


@router.post("/start")
async def start_interview(data: StartInterviewRequest):
    """Start a new interview simulation session."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{session_id}/submit-audio")
async def submit_audio(session_id: str):
    """Submit audio response for AI evaluation."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{session_id}/feedback")
async def get_feedback(session_id: str):
    """Get AI-generated feedback for interview."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/history")
async def interview_history():
    """Get past interview sessions."""
    raise HTTPException(status_code=501, detail="Not implemented")
