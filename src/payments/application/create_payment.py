from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from payments.application.ports.clock import Clock
from payments.application.common.handler import Handler
from payments.application.ports.event_collector import EventCollector
from payments.application.ports.event_publisher import EventPublisher
from payments.application.ports.payment_gateway import PaymentGateway
from payments.application.ports.transaction_manager import TransactionManager
from payments.application.ports.uuid_generator import UUIDGenerator
from payments.domain.entities.payment import Payment, PaymentId
from payments.domain.value_objects.currency import Currency
from payments.domain.value_objects.payment_status import PaymentStatus



@dataclass(frozen=True, kw_only=True, slots=True)
class CreatePaymentCommand:
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]


@dataclass(frozen=True, kw_only=True, slots=True)
class CreatePaymentResult:
    payment_id: PaymentId
    status: PaymentStatus
    created_at: datetime


class CreatePaymentHandler(Handler):

    def __init__(
        self,
        clock: Clock,
        uuid_generator: UUIDGenerator,
        payment_gateway: PaymentGateway,
        event_publisher: EventPublisher,
        event_collector: EventCollector,
        transaction_manager: TransactionManager,
    ) -> None:
        self._clock = clock
        self._uuid_generator = uuid_generator
        self._payment_gateway = payment_gateway
        self._event_publisher = event_publisher
        self._event_collector = event_collector
        self._transaction_manager = transaction_manager

    async def __call__(self, command: CreatePaymentCommand) -> CreatePaymentResult:
        created_at = self._clock.now()
        payment, payment_created = Payment.create(
            oid=PaymentId(self._uuid_generator()),
            amount=command.amount,
            currency=command.currency,
            description=command.description,
            metadata=command.metadata,
            status=PaymentStatus.PENDING,
            created_at=created_at,
            updated_at=created_at,
        )

        self._event_collector.add(payment_created)
        self._payment_gateway.add(payment)
        await self._event_publisher.publish(*self._event_collector.collect())
        await self._transaction_manager.commit()

        return CreatePaymentResult(
            payment_id=payment.oid,
            status=payment.status,
            created_at=created_at,
        )
