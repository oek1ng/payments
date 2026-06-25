"""AMQP integration tests for the payments listener."""

from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
from dishka import AsyncContainer, Provider, Scope, provide
from dishka_faststream import setup_dishka
from faststream import FastStream
from faststream.rabbit import RabbitBroker, TestRabbitBroker
from sqlalchemy.ext.asyncio import AsyncSession

from payments.application.ports.clock import Clock
from payments.application.ports.uuid_generator import UUIDGenerator
from payments.application.ports.webhook_client import WebhookClient
from payments.application.update_payment_status import UpdatePaymentStatusHandler
from payments.domain.entities.payment import Payment
from payments.domain.entities.payment_id import PaymentId
from payments.domain.value_objects.currency import Currency
from payments.domain.value_objects.payment_status import PaymentStatus
from payments.infrastructure.amqp import PAYMENTS_EXCHANGE
from payments.main.di import create_container
from payments.presentation.api.amqp.v1.router import router
from tests.conftest import requires_pg
from tests.service.conftest import _TestSessionProvider


class FakeWebhookClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def send(self, url: str, payload: dict[str, object]) -> None:
        self.calls.append((url, payload))


class ListenerHandlerProviderMock(Provider):
    scope = Scope.REQUEST

    def __init__(self, webhook_client: FakeWebhookClient) -> None:
        super().__init__()
        self._webhook_client = webhook_client

    handler = provide(UpdatePaymentStatusHandler)

    @provide(provides=WebhookClient)
    async def webhook(self) -> FakeWebhookClient:
        return self._webhook_client


@pytest.fixture
def webhook_client() -> FakeWebhookClient:
    return FakeWebhookClient()


@pytest.fixture
async def amqp_container(
    session: AsyncSession,
    webhook_client: FakeWebhookClient,
) -> AsyncGenerator[AsyncContainer]:
    c = create_container(
        _TestSessionProvider(session),
        ListenerHandlerProviderMock(webhook_client),
    )
    yield c
    await c.close()


@pytest.fixture
def broker(amqp_container: AsyncContainer) -> RabbitBroker:
    b = RabbitBroker("amqp://localhost:5672/")
    b.include_router(router)
    app = FastStream(b)
    setup_dishka(amqp_container, app)
    return b


@pytest.fixture
async def uuid_generator(amqp_container: AsyncContainer) -> UUIDGenerator:
    async with amqp_container() as ctx:
        return await ctx.get(UUIDGenerator)  # type: ignore[no-any-return]


@pytest.fixture
async def clock(amqp_container: AsyncContainer) -> Clock:
    async with amqp_container() as ctx:
        return await ctx.get(Clock)  # type: ignore[no-any-return]


@requires_pg
async def test_on_payment_processed_updates_status(
    session: AsyncSession,
    broker: RabbitBroker,
    webhook_client: FakeWebhookClient,
    uuid_generator: UUIDGenerator,
    clock: Clock,
) -> None:
    now = clock.now()
    payment_id = PaymentId(uuid_generator())

    payment = Payment(
        oid=payment_id,
        amount=Decimal("100.00"),
        currency=Currency.RUB,
        description="Test",
        idempotency_key=f"test-{uuid_generator()}",
        webhook_url="https://example.com/webhook",
        metadata={},
        status=PaymentStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    session.add(payment)
    await session.flush()

    payload = {"payment_id": str(payment_id), "status": "succeeded"}

    async with TestRabbitBroker(broker) as test_broker:
        await test_broker.publish(
            payload,
            routing_key="payments.processed",
            exchange=PAYMENTS_EXCHANGE,
        )

    await session.refresh(payment)
    assert payment.status == PaymentStatus.SUCCEEDED
    assert len(webhook_client.calls) == 1
    assert webhook_client.calls[0][0] == "https://example.com/webhook"


@requires_pg
async def test_on_payment_processed_rejects_invalid_message(
    broker: RabbitBroker,
    webhook_client: FakeWebhookClient,
) -> None:
    async with TestRabbitBroker(broker) as test_broker:
        await test_broker.publish(
            {"invalid": "data"},
            routing_key="payments.processed",
            exchange=PAYMENTS_EXCHANGE,
        )

    assert len(webhook_client.calls) == 0
