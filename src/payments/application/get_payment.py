from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from payments.application.common.handler import Handler
from payments.application.ports.payment_gateway import PaymentGateway
from payments.domain.entities.payment import PaymentId
from payments.domain.value_objects.currency import Currency
from payments.domain.value_objects.payment_status import PaymentStatus


@dataclass(frozen=True, kw_only=True, slots=True)
class GetPaymentCommand:
    payment_id: PaymentId


@dataclass(frozen=True, kw_only=True, slots=True)
class GetPaymentResult:
    id: PaymentId
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime


class CreatePaymentHandler(Handler):

    def __init__(
        self,
        payment_gateway: PaymentGateway,
    ) -> None:
        self._payment_gateway = payment_gateway

    async def __call__(self, command: GetPaymentCommand) -> GetPaymentResult:
        payment = await self._payment_gateway.get(command.payment_id)

        return GetPaymentResult(
            id=payment.oid,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=payment.metadata,
            status=payment.status,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )
