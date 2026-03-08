from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/mentors")
async def list_mentors():
    """List available mentors with filters."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/mentors/{mentor_id}")
async def get_mentor(mentor_id: str):
    """Get mentor profile."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/request")
async def request_session():
    """Request a mentorship session."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{session_id}/rate")
async def rate_session(session_id: str):
    """Rate a completed mentorship session."""
    raise HTTPException(status_code=501, detail="Not implemented")
