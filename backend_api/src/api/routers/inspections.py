from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from src.api.core.security import get_current_user_token_data
from src.api.models.domain import InspectionStubCreateRequest
from src.api.services.audit_service import write_audit_log

router = APIRouter(prefix="/inspections", tags=["inspections"])


class InspectionStubResponse(BaseModel):
    inspection_id: str = Field(..., description="Inspection id (stub).")
    status: str = Field(..., description="Inspection status (stub).")


@router.post(
    "",
    response_model=InspectionStubResponse,
    summary="Create inspection (stub)",
    description="Create an inspection record (stub) for an application.",
    operation_id="inspections_create_stub",
)
def create_inspection(req: InspectionStubCreateRequest, token_data=Depends(get_current_user_token_data), request: Request = None):
    """Create inspection (stub)."""
    inspection_id = f"ins_{req.application_id}"
    write_audit_log(
        actor_user_id=token_data.user_id,
        action="inspections.create",
        entity_type="inspection",
        entity_id=inspection_id,
        metadata={"application_id": req.application_id},
        request=request,
    )
    return InspectionStubResponse(inspection_id=inspection_id, status="scheduled")
