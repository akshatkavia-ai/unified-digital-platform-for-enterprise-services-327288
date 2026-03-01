from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address (unique).")
    password: str = Field(..., min_length=8, description="User password (min length 8).")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email.")
    password: str = Field(..., description="User password.")
    mfa_code: Optional[str] = Field(
        default=None,
        description="MFA code (scaffolding). When MFA is enabled for user, this must be provided.",
    )


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token.")
    token_type: str = Field(default="bearer", description="Token type.")


class TokenData(BaseModel):
    user_id: str = Field(..., description="User id (UUID string).")
    claims: Dict[str, Any] = Field(default_factory=dict, description="Decoded token claims.")


class MFAEnrollResponse(BaseModel):
    mfa_enabled: bool = Field(..., description="Whether MFA is enabled after this operation.")
    provisioning_uri: Optional[str] = Field(
        default=None,
        description="Provisioning URI/QR payload for authenticator apps (stub/scaffolding).",
    )
