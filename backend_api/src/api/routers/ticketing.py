from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src.api.core.db import db_conn_cursor, get_database_config
from src.api.core.security import get_current_user_token_data
from src.api.models.domain import TicketCreateRequest
from src.api.services.audit_service import write_audit_log

router = APIRouter(prefix="/tickets", tags=["ticketing"])


class TicketResponse(BaseModel):
    ticket_id: str = Field(..., description="Ticket id.")
    status: str = Field(..., description="Ticket status.")


@router.post(
    "",
    response_model=TicketResponse,
    summary="Create ticket",
    description="Create a helpdesk ticket (Postgres-backed).",
    operation_id="tickets_create",
)
def create_ticket(req: TicketCreateRequest, token_data=Depends(get_current_user_token_data), request: Request = None):
    """Create ticket (Postgres-backed)."""
    cfg = get_database_config()
    with db_conn_cursor(cfg.dsn) as (_, cur):
        cur.execute(
            """
            INSERT INTO tickets (subject, description, category, priority, status, created_by_user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, status
            """,
            (req.subject, req.description, req.category, req.priority, "open", token_data.user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create ticket")

    ticket_id = str(row["id"])
    write_audit_log(
        actor_user_id=token_data.user_id,
        action="tickets.create",
        entity_type="ticket",
        entity_id=ticket_id,
        metadata={"subject": req.subject, "category": req.category, "priority": req.priority},
        request=request,
    )
    return TicketResponse(ticket_id=ticket_id, status=row["status"])
