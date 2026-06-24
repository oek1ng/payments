"""Get payment use case."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from payments.application.ports.payment_gateway import PaymentGateway
from payments.domain.entities.payment import PaymentId
from payments.domain.value_objects.currency import Currency
from payments.domain.value_objects.payment_status import PaymentStatus


@dataclass(frozen=True, kw_only=True, slots=True)
class GetPaymentCommand:
    """Command to retrieve a payment by ID."""

    payment_id: PaymentId


@dataclass(frozen=True, kw_only=True, slots=True)
class GetPaymentResult:
    """Result containing payment details."""

    id: PaymentId
    amount: Decimal
    currency: Currency
    description: str
    idempotency_key: str
    webhook_url: str
    metadata: dict[str, Any]
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime


class GetPaymentHandler:
    """Handles retrieval of a payment by ID."""

    def __init__(
        self,
        payment_gateway: PaymentGateway,
    ) -> None:
        """Initialize the handler with required dependencies."""
        self._payment_gateway = payment_gateway

    async def __call__(self, command: GetPaymentCommand) -> GetPaymentResult:
        """Process the payment retrieval command.

        Returns:
            The result containing the payment details.

        """
        payment = await self._payment_gateway.get_by_id(command.payment_id)

        return GetPaymentResult(
            id=payment.oid,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            idempotency_key=payment.idempotency_key,
            webhook_url=payment.webhook_url,
            metadata=payment.metadata,
            status=payment.status,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )
