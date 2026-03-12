from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "student"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest):
    """Register a new user and return JWT tokens."""
    # TODO: implement user creation with hashed password
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """Authenticate user and return JWT tokens."""
    # TODO: verify credentials, return tokens
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token():
    """Refresh access token using refresh token."""
    # TODO: validate refresh token, issue new pair
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/me")
async def get_current_user():
    """Get current authenticated user profile."""
    # TODO: decode JWT, return user info
    raise HTTPException(status_code=501, detail="Not implemented")
