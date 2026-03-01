from datetime import datetime, timezone
from typing import Dict
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request

from src.api.core.security import get_current_user_token_data
from src.api.models.domain import ApplicationCreateRequest, ApplicationResponse
from src.api.services.audit_service import write_audit_log

router = APIRouter(prefix="/applications", tags=["applications"])

# Minimal stub store; replace with Postgres tables in later steps.
_APPLICATIONS: Dict[UUID, ApplicationResponse] = {}


@router.post(
    "",
    response_model=ApplicationResponse,
    summary="Create application",
    description="Create a new application (stub persistence) and emit audit log.",
    operation_id="applications_create",
)
def create_application(
    req: ApplicationCreateRequest,
    token_data=Depends(get_current_user_token_data),
    request: Request = None,
):
    """Create an application (stub)."""
    app_id = uuid4()
    created = ApplicationResponse(
        id=app_id,
        status="submitted",
        applicant_name=req.applicant_name,
        service_code=req.service_code,
        created_at=datetime.now(timezone.utc),
    )
    _APPLICATIONS[app_id] = created

    write_audit_log(
        actor_user_id=token_data.user_id,
        action="applications.create",
        entity_type="application",
        entity_id=str(app_id),
        metadata={"service_code": req.service_code},
        request=request,
    )
    return created


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Get application",
    description="Fetch an application by id (stub).",
    operation_id="applications_get",
)
def get_application(application_id: UUID, token_data=Depends(get_current_user_token_data)):
    """Get application (stub)."""
    return _APPLICATIONS[application_id]
