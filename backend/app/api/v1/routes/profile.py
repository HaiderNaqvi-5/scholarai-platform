from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("")
async def get_profile():
    """Get current student profile."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("")
async def update_profile():
    """Update student profile fields."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/sop")
async def upload_sop():
    """Upload or update SOP draft."""
    raise HTTPException(status_code=501, detail="Not implemented")
