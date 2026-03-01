from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from src.api.core.security import get_current_user_token_data
from src.api.models.domain import PaymentInitRequest
from src.api.services.audit_service import write_audit_log

router = APIRouter(prefix="/payments", tags=["payments"])


class PaymentInitResponse(BaseModel):
    payment_id: str = Field(..., description="Payment id (stub).")
    gateway_redirect_url: str = Field(..., description="Redirect URL to payment gateway (stub).")
    status: str = Field(..., description="Status of payment initialization.")


@router.post(
    "/init",
    response_model=PaymentInitResponse,
    summary="Initialize payment (stub)",
    description="Boundary stub for payment gateway initiation. Does not call external provider yet.",
    operation_id="payments_init_stub",
)
def init_payment(req: PaymentInitRequest, token_data=Depends(get_current_user_token_data), request: Request = None):
    """Initialize payment (stub)."""
    payment_id = "pay_stub_001"
    write_audit_log(
        actor_user_id=token_data.user_id,
        action="payments.init",
        entity_type="payment",
        entity_id=payment_id,
        metadata={"reference_type": req.reference_type, "reference_id": req.reference_id, "amount_paise": req.amount_paise, "currency": req.currency},
        request=request,
    )
    return PaymentInitResponse(payment_id=payment_id, gateway_redirect_url="https://example.invalid/pay", status="created")
