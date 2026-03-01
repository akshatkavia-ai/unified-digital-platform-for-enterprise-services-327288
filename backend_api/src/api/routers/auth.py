from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from src.api.core.security import get_current_user_token_data
from src.api.models.auth import LoginRequest, MFAEnrollResponse, RegisterRequest, TokenResponse
from src.api.services.audit_service import write_audit_log
from src.api.services.auth_service import authenticate_user, enroll_mfa_stub, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


class MeResponse(BaseModel):
    user_id: str = Field(..., description="Authenticated user id.")
    claims: dict = Field(default_factory=dict, description="Token claims.")


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Register new user",
    description="Create a new user account and return an access token.",
    operation_id="auth_register",
)
def register(req: RegisterRequest, request: Request):
    """Register endpoint.

    Parameters:
      - req: email + password

    Returns:
      - TokenResponse with access_token
    """
    user = register_user(email=req.email, password=req.password)
    token = authenticate_user(email=req.email, password=req.password, mfa_code=None)
    write_audit_log(
        actor_user_id=str(user.id),
        action="auth.register",
        entity_type="user",
        entity_id=str(user.id),
        metadata={"email": req.email},
        request=request,
    )
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticate with email/password and return an access token. MFA code required if MFA enabled (scaffolding).",
    operation_id="auth_login",
)
def login(req: LoginRequest, request: Request):
    """Login endpoint."""
    token = authenticate_user(email=req.email, password=req.password, mfa_code=req.mfa_code)
    # We intentionally avoid coupling to user_id extraction here; audit still records the attempt.
    write_audit_log(actor_user_id=None, action="auth.login", metadata={"email": req.email}, request=request)
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current user info",
    description="Return user id and claims from bearer token.",
    operation_id="auth_me",
)
def me(token_data=Depends(get_current_user_token_data)):
    """Me endpoint."""
    return MeResponse(user_id=token_data.user_id, claims=token_data.claims)


@router.post(
    "/mfa/enroll",
    response_model=MFAEnrollResponse,
    summary="Enroll MFA (scaffolding)",
    description="Enable MFA for current user and return a placeholder provisioning URI (stub).",
    operation_id="auth_mfa_enroll",
)
def mfa_enroll(token_data=Depends(get_current_user_token_data), request: Request = None):
    """MFA enroll (stub)."""
    result = enroll_mfa_stub(user_id=token_data.user_id)
    write_audit_log(
        actor_user_id=token_data.user_id,
        action="auth.mfa.enroll",
        entity_type="user",
        entity_id=token_data.user_id,
        metadata={"mfa_enabled": result["mfa_enabled"]},
        request=request,
    )
    return MFAEnrollResponse(mfa_enabled=result["mfa_enabled"], provisioning_uri=result["provisioning_uri"])
