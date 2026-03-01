from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src.api.core.db import db_conn_cursor, get_database_config
from src.api.core.security import get_current_user_token_data
from src.api.models.domain import PaymentInitRequest
from src.api.services.audit_service import write_audit_log

router = APIRouter(prefix="/payments", tags=["payments"])


class PaymentInitResponse(BaseModel):
    payment_id: str = Field(..., description="Payment id.")
    gateway_redirect_url: str = Field(..., description="Redirect URL to payment gateway (stub URL for now).")
    status: str = Field(..., description="Status of payment initialization.")


@router.post(
    "/init",
    response_model=PaymentInitResponse,
    summary="Initialize payment",
    description="Persist a payment initialization request in Postgres (gateway integration stubbed).",
    operation_id="payments_init",
)
def init_payment(req: PaymentInitRequest, token_data=Depends(get_current_user_token_data), request: Request = None):
    """Initialize payment (Postgres-backed; external gateway is stubbed)."""
    # Gateway integration is out of scope; we still persist and return a placeholder redirect url.
    redirect_url = "https://example.invalid/pay"

    cfg = get_database_config()
    with db_conn_cursor(cfg.dsn) as (_, cur):
        cur.execute(
            """
            INSERT INTO payments (
              reference_type, reference_id, amount_paise, currency, status, gateway_redirect_url, created_by_user_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, status, gateway_redirect_url
            """,
            (
                req.reference_type,
                req.reference_id,
                req.amount_paise,
                req.currency,
                "created",
                redirect_url,
                token_data.user_id,
            ),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to initialize payment")

    payment_id = str(row["id"])
    write_audit_log(
        actor_user_id=token_data.user_id,
        action="payments.init",
        entity_type="payment",
        entity_id=payment_id,
        metadata={
            "reference_type": req.reference_type,
            "reference_id": req.reference_id,
            "amount_paise": req.amount_paise,
            "currency": req.currency,
        },
        request=request,
    )
    return PaymentInitResponse(payment_id=payment_id, gateway_redirect_url=row["gateway_redirect_url"], status=row["status"])
