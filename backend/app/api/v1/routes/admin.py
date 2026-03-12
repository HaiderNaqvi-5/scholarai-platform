from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/users")
async def list_users():
    """List and search all users."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/users/{user_id}/status")
async def update_user_status(user_id: str):
    """Activate or deactivate a user."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/mentors/pending")
async def pending_mentors():
    """List pending mentor approvals."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/mentors/{mentor_id}/approve")
async def approve_mentor(mentor_id: str):
    """Approve or reject a mentor application."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/scrapers")
async def scraper_history():
    """Get scraper run history."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/scrapers/trigger")
async def trigger_scraper():
    """Manually trigger a scraper run."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/analytics")
async def platform_analytics():
    """Get platform analytics and metrics."""
    raise HTTPException(status_code=501, detail="Not implemented")
