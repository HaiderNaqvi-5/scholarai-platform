from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/queue")
async def get_curation_queue() -> dict[str, str]:
    raise HTTPException(
        status_code=501,
        detail="Curation queue APIs are reserved for internal workflows after the foundation phase",
    )


@router.post("/{record_id}/validate")
async def validate_record(record_id: str) -> dict[str, str]:
    raise HTTPException(
        status_code=501,
        detail=f"Validation workflow for {record_id} is not active yet",
    )


@router.post("/{record_id}/publish")
async def publish_record(record_id: str) -> dict[str, str]:
    raise HTTPException(
        status_code=501,
        detail=f"Publish workflow for {record_id} is not active yet",
    )
