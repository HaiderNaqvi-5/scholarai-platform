from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("")
async def create_document() -> dict[str, str]:
    raise HTTPException(
        status_code=501,
        detail="Document workflows are deferred in the foundation phase",
    )


@router.post("/{document_id}/feedback")
async def request_document_feedback(document_id: str) -> dict[str, str]:
    raise HTTPException(
        status_code=501,
        detail=f"Document feedback for {document_id} is deferred in the foundation phase",
    )
