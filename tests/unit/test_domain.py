from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from payments.domain.entities.payment import Payment
from payments.domain.entities.payment_id import PaymentId
from payments.domain.value_objects.currency import Currency
from payments.domain.value_objects.payment_status import PaymentStatus


def test_create_payment_emits_event() -> None:
    payment_id = PaymentId(uuid4())
    amount = Decimal("100.00")
    currency = Currency.RUB
    now = datetime.now(tz=UTC)

    payment, event = Payment.create(
        oid=payment_id,
        amount=amount,
        currency=currency,
        description="Order #42",
        idempotency_key="key-1",
        webhook_url="https://example.com/webhook",
        metadata={"order_id": 42},
        status=PaymentStatus.PENDING,
        created_at=now,
        updated_at=now,
    )

    assert payment.oid == payment_id
    assert payment.amount == amount
    assert payment.status == PaymentStatus.PENDING
    assert event.id == payment_id
    assert event.status == PaymentStatus.PENDING


def test_mark_succeeded_updates_status() -> None:
    payment_id = PaymentId(uuid4())
    now = datetime.now(tz=UTC)

    payment, _ = Payment.create(
        oid=payment_id,
        amount=Decimal("50.00"),
        currency=Currency.USD,
        description="Test",
        idempotency_key="key-2",
        webhook_url="https://example.com/webhook",
        metadata={},
        status=PaymentStatus.PENDING,
        created_at=now,
        updated_at=now,
    )

    payment.mark_succeeded(now)

    assert payment.status == PaymentStatus.SUCCEEDED


def test_mark_failed_updates_status() -> None:
    payment_id = PaymentId(uuid4())
    now = datetime.now(tz=UTC)

    payment, _ = Payment.create(
        oid=payment_id,
        amount=Decimal("75.00"),
        currency=Currency.EUR,
        description="Test",
        idempotency_key="key-3",
        webhook_url="https://example.com/webhook",
        metadata={},
        status=PaymentStatus.PENDING,
        created_at=now,
        updated_at=now,
    )

    payment.mark_failed(now)

    assert payment.status == PaymentStatus.FAILED
