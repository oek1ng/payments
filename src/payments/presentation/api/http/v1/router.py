"""FastAPI router for payment endpoints."""

from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Header

from payments.application.create_payment import (
    CreatePaymentCommand,
    CreatePaymentHandler,
)
from payments.application.get_payment import GetPaymentCommand, GetPaymentHandler
from payments.domain.entities.payment import PaymentId
from payments.presentation.api.http.v1.schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    GetPaymentResponse,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/", status_code=202)
@inject
async def create_payment(
    body: CreatePaymentRequest,
    handler: FromDishka[CreatePaymentHandler],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> CreatePaymentResponse:
    """Create a new payment.

    Returns:
        The created payment details.

    """
    command = CreatePaymentCommand(
        amount=body.amount,
        currency=body.currency,
        description=body.description,
        idempotency_key=idempotency_key,
        webhook_url=body.webhook_url,
        metadata=body.metadata,
    )
    result = await handler(command)
    return CreatePaymentResponse(
        payment_id=result.payment_id,
        status=result.status,
        created_at=result.created_at,
    )


@router.get("/{payment_id}")
@inject
async def get_payment(
    payment_id: UUID,
    handler: FromDishka[GetPaymentHandler],
) -> GetPaymentResponse:
    """Get payment details by ID.

    Returns:
        The payment details.

    """
    command = GetPaymentCommand(payment_id=PaymentId(payment_id))
    result = await handler(command)
    return GetPaymentResponse(
        id=result.id,
        amount=result.amount,
        currency=result.currency,
        description=result.description,
        idempotency_key=result.idempotency_key,
        webhook_url=result.webhook_url,
        metadata=result.metadata,
        status=result.status,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
