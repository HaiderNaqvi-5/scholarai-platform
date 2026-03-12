from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class MatchFilter(BaseModel):
    countries: Optional[List[str]] = None
    degree_level: Optional[str] = None
    min_funding: Optional[float] = None
    deadline_after: Optional[str] = None


class MatchRequest(BaseModel):
    student_id: str
    filters: Optional[MatchFilter] = None
    limit: int = 20


@router.get("")
async def list_scholarships(page: int = 1, per_page: int = 20):
    """List scholarships with pagination and filters."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{scholarship_id}")
async def get_scholarship(scholarship_id: str):
    """Get scholarship details by ID."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/match")
async def match_scholarships(data: MatchRequest):
    """AI-powered scholarship matching with ranked results."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{scholarship_id}/explanation")
async def get_explanation(scholarship_id: str):
    """Get SHAP explanation for a match score."""
    raise HTTPException(status_code=501, detail="Not implemented")
