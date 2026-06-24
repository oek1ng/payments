from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Self

from payments.domain.entities.payment import Payment, PaymentId
from payments.domain.events.base import Event
from payments.domain.value_objects.currency import Currency
from payments.domain.value_objects.payment_status import PaymentStatus


@dataclass(frozen=True, kw_only=True, slots=True)
class PaymentCreated(Event[Payment]):
    id: PaymentId
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, entity: Payment) -> Self:
        return cls(
            id=entity.oid,
            amount=entity.amount,
            currency=entity.currency,
            description=entity.description,
            metadata=entity.metadata,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
