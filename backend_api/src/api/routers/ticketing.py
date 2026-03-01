from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from src.api.core.security import get_current_user_token_data
from src.api.models.domain import TicketCreateRequest
from src.api.services.audit_service import write_audit_log

router = APIRouter(prefix="/tickets", tags=["ticketing"])


class TicketResponse(BaseModel):
    ticket_id: str = Field(..., description="Ticket id (stub).")
    status: str = Field(..., description="Ticket status.")


@router.post(
    "",
    response_model=TicketResponse,
    summary="Create ticket",
    description="Create a helpdesk ticket (stub boundary).",
    operation_id="tickets_create",
)
def create_ticket(req: TicketCreateRequest, token_data=Depends(get_current_user_token_data), request: Request = None):
    """Create ticket (stub)."""
    ticket_id = "tkt_stub_001"
    write_audit_log(
        actor_user_id=token_data.user_id,
        action="tickets.create",
        entity_type="ticket",
        entity_id=ticket_id,
        metadata={"subject": req.subject, "category": req.category, "priority": req.priority},
        request=request,
    )
    return TicketResponse(ticket_id=ticket_id, status="open")
