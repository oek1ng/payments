from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, NewType, Self
from uuid import UUID

from payments.domain.entities.base import Entity
from payments.domain.events.payment_created import PaymentCreated
from payments.domain.value_objects.currency import Currency
from payments.domain.value_objects.payment_status import PaymentStatus

PaymentId = NewType("PaymentId", UUID)


@dataclass(kw_only=True, eq=False)
class Payment(Entity[PaymentId]):
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        oid: PaymentId,
        amount: Decimal,
        currency: Currency,
        description: str,
        metadata: dict[str, Any],
        status: PaymentStatus,
        created_at: datetime,
        updated_at: datetime,
    ) -> tuple[Self, PaymentCreated]:
        payment = cls(
                oid=oid,
                amount=amount,
                currency=currency,
                description=description,
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
        self.status = PaymentStatus.SUCCEEDED
        self.updated_at = updated_at

    def mark_failed(self, updated_at: datetime) -> None:
        self.status = PaymentStatus.FAILED
        self.updated_at = updated_at

    def mark_pending(self) -> None:
        self.status = PaymentStatus.PENDING
        self.updated_at = self.updated_at
