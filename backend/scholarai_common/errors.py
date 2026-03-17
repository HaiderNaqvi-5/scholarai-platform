from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel

class ErrorCode(str, Enum):
    AUTH_INVALID_CREDENTIALS = "auth_invalid_credentials"
    AUTH_INACTIVE_ACCOUNT = "auth_inactive_account"
    AUTH_TOKEN_EXPIRED = "auth_token_expired"
    AUTH_TOKEN_REVOKED = "auth_token_revoked"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    INTERNAL_SERVER_ERROR = "internal_server_error"

class ScholarAIErrorResponse(BaseModel):
    code: ErrorCode
    message: str
    detail: Optional[Any] = None

class ScholarAIException(Exception):
    def __init__(
        self, 
        code: ErrorCode, 
        message: str, 
        status_code: int = 400,
        detail: Optional[Any] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)
