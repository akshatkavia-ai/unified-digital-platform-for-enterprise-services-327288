from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.core.db import db_conn_cursor, get_database_config
from src.api.core.security import get_current_user_token_data
from src.api.models.domain import ApplicationCreateRequest, ApplicationResponse
from src.api.services.audit_service import write_audit_log

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post(
    "",
    response_model=ApplicationResponse,
    summary="Create application",
    description="Create a new application and persist it to Postgres.",
    operation_id="applications_create",
)
def create_application(
    req: ApplicationCreateRequest,
    token_data=Depends(get_current_user_token_data),
    request: Request = None,
):
    """Create an application (Postgres-backed)."""
    cfg = get_database_config()
    with db_conn_cursor(cfg.dsn) as (_, cur):
        cur.execute(
            """
            INSERT INTO applications (applicant_name, service_code, status, payload, created_by_user_id)
            VALUES (%s, %s, %s, %s::jsonb, %s)
            RETURNING id, status, applicant_name, service_code, created_at
            """,
            (req.applicant_name, req.service_code, "submitted", __import__("json").dumps(req.payload), token_data.user_id),
        )
        row = cur.fetchone()

    created = ApplicationResponse(
        id=UUID(str(row["id"])),
        status=row["status"],
        applicant_name=row["applicant_name"],
        service_code=row["service_code"],
        created_at=row["created_at"].astimezone(timezone.utc) if isinstance(row["created_at"], datetime) else row["created_at"],
    )

    write_audit_log(
        actor_user_id=token_data.user_id,
        action="applications.create",
        entity_type="application",
        entity_id=str(created.id),
        metadata={"service_code": req.service_code},
        request=request,
    )
    return created


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Get application",
    description="Fetch an application by id from Postgres.",
    operation_id="applications_get",
)
def get_application(application_id: UUID, token_data=Depends(get_current_user_token_data)):
    """Get application (Postgres-backed)."""
    cfg = get_database_config()
    with db_conn_cursor(cfg.dsn) as (_, cur):
        cur.execute(
            "SELECT id, status, applicant_name, service_code, created_at FROM applications WHERE id=%s",
            (str(application_id),),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")

    return ApplicationResponse(
        id=UUID(str(row["id"])),
        status=row["status"],
        applicant_name=row["applicant_name"],
        service_code=row["service_code"],
        created_at=row["created_at"],
    )
