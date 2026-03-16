from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/upload")
async def upload_credential():
    """Upload a document for verification."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("")
async def list_credentials():
    """List student's credentials."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{credential_id}/verify")
async def verify_credential(credential_id: str):
    """Institution verifies a document."""
    raise HTTPException(status_code=501, detail="Not implemented")
