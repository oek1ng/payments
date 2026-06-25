"""Payment aggregate root."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Self

from payments.domain.entities.base import Entity
from payments.domain.entities.payment_id import PaymentId
from payments.domain.events.payment_created import PaymentCreated
from payments.domain.value_objects.currency import Currency
from payments.domain.value_objects.payment_status import PaymentStatus


@dataclass(kw_only=True, eq=False)
class Payment(Entity[PaymentId]):
    """Payment aggregate root representing a financial transaction."""

    amount: Decimal
    currency: Currency
    description: str
    idempotency_key: str
    webhook_url: str
    metadata: dict[str, Any]
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(  # noqa: PLR0917
        cls,
        oid: PaymentId,
        amount: Decimal,
        currency: Currency,
        description: str,
        idempotency_key: str,
        webhook_url: str,
        metadata: dict[str, Any],
        status: PaymentStatus,
        created_at: datetime,
        updated_at: datetime,
    ) -> tuple[Self, PaymentCreated]:
        """Create a new payment and its corresponding event.

        Returns:
            A tuple of the created payment and its creation event.

        """
        payment = cls(
            oid=oid,
            amount=amount,
            currency=currency,
            description=description,
            idempotency_key=idempotency_key,
            webhook_url=webhook_url,
            metadata=metadata,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
        )
        return (
            payment,
            PaymentCreated.of(payment),
        )

    def mark_succeeded(self, updated_at: datetime) -> None:
        """Mark the payment as succeeded."""
        self.status = PaymentStatus.SUCCEEDED
        self.updated_at = updated_at

    def mark_failed(self, updated_at: datetime) -> None:
        """Mark the payment as failed."""
        self.status = PaymentStatus.FAILED
        self.updated_at = updated_at

    def mark_pending(self, updated_at: datetime) -> None:
        """Revert the payment status to pending."""
        self.status = PaymentStatus.PENDING
        self.updated_at = updated_at
