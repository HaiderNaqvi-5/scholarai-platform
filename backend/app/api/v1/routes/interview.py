from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("")
async def create_interview_session() -> dict[str, str]:
    raise HTTPException(
        status_code=501,
        detail="Interview practice is deferred until after the first vertical slice",
    )


@router.post("/{session_id}/responses")
async def submit_interview_response(session_id: str) -> dict[str, str]:
    raise HTTPException(
        status_code=501,
        detail=f"Interview response handling for {session_id} is deferred",
    )


@router.get("/{session_id}")
async def get_interview_session(session_id: str) -> dict[str, str]:
    raise HTTPException(
        status_code=501,
        detail=f"Interview feedback for {session_id} is deferred",
    )
