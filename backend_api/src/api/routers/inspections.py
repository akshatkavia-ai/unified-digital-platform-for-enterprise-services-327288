from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src.api.core.db import db_conn_cursor, get_database_config
from src.api.core.security import get_current_user_token_data
from src.api.models.domain import InspectionStubCreateRequest
from src.api.services.audit_service import write_audit_log

router = APIRouter(prefix="/inspections", tags=["inspections"])


class InspectionStubResponse(BaseModel):
    inspection_id: str = Field(..., description="Inspection id.")
    status: str = Field(..., description="Inspection status.")


@router.post(
    "",
    response_model=InspectionStubResponse,
    summary="Create inspection",
    description="Create an inspection record for an application (Postgres-backed).",
    operation_id="inspections_create",
)
def create_inspection(req: InspectionStubCreateRequest, token_data=Depends(get_current_user_token_data), request: Request = None):
    """Create inspection (Postgres-backed)."""
    cfg = get_database_config()
    with db_conn_cursor(cfg.dsn) as (_, cur):
        cur.execute(
            """
            INSERT INTO inspections (
              application_id, location_text, scheduled_at, status, created_by_user_id
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, status
            """,
            (req.application_id, req.location_text, req.scheduled_at, "scheduled", token_data.user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create inspection")

    inspection_id = str(row["id"])
    write_audit_log(
        actor_user_id=token_data.user_id,
        action="inspections.create",
        entity_type="inspection",
        entity_id=inspection_id,
        metadata={"application_id": req.application_id},
        request=request,
    )
    return InspectionStubResponse(inspection_id=inspection_id, status=row["status"])
