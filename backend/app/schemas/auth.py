"""
Authentication schemas - Login, Token, OAuth2
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """Login request with email/username and password"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!"
            }
        }


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefreshRequest(BaseModel):
    """Request to refresh access token"""
    refresh_token: str


class TokenData(BaseModel):
    """Data extracted from JWT token"""
    user_id: Optional[int] = None
    email: Optional[str] = None
    roles: list[str] = []


class PasswordChangeRequest(BaseModel):
    """Request to change password"""
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    """Request password reset link"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token"""
    token: str
    new_password: str
