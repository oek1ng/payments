"""Unit tests for application handlers using real DI container."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

import pytest
from dishka import AsyncContainer
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from payments.application.common.exceptions import IdempotencyKeyConflictError
from payments.application.create_payment import (
    CreatePaymentCommand,
    CreatePaymentHandler,
)
from payments.application.get_payment import GetPaymentCommand, GetPaymentHandler
from payments.domain.entities.payment import Payment
from payments.domain.entities.payment_id import PaymentId
from payments.domain.value_objects.currency import Currency
from payments.domain.value_objects.payment_status import PaymentStatus
from payments.infrastructure.persistence.tables.payments import payments_table
from tests.conftest import requires_pg


@requires_pg
async def test_create_payment_returns_pending_payment(
    container: AsyncContainer,
    session: AsyncSession,
) -> None:
    async with container() as ctx:
        handler = await ctx.get(CreatePaymentHandler)

    result = await handler(
        CreatePaymentCommand(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            description="Order",
            idempotency_key="key-1",
            webhook_url="https://example.com/webhook",
            metadata={},
        ),
    )

    assert result.status == PaymentStatus.PENDING
    assert isinstance(result.payment_id, UUID)
    assert isinstance(result.created_at, datetime)

    stmt = select(Payment).where(payments_table.c.id == result.payment_id)
    db_payment = (await session.execute(stmt)).scalar_one()
    assert db_payment.amount == Decimal("100.00")


@requires_pg
async def test_create_payment_idempotent_returns_existing(
    container: AsyncContainer,
) -> None:
    async with container() as ctx:
        handler = await ctx.get(CreatePaymentHandler)

    first = await handler(
        CreatePaymentCommand(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            description="Order",
            idempotency_key="key-1",
            webhook_url="https://example.com/webhook",
            metadata={},
        ),
    )
    second = await handler(
        CreatePaymentCommand(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            description="Order",
            idempotency_key="key-1",
            webhook_url="https://example.com/webhook",
            metadata={},
        ),
    )

    assert second.payment_id == first.payment_id


@requires_pg
async def test_create_payment_different_body_same_key_raises_conflict(
    container: AsyncContainer,
) -> None:
    async with container() as ctx:
        handler = await ctx.get(CreatePaymentHandler)

    await handler(
        CreatePaymentCommand(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            description="Order",
            idempotency_key="key-1",
            webhook_url="https://example.com/webhook",
            metadata={},
        ),
    )

    with pytest.raises(IdempotencyKeyConflictError):
        await handler(
            CreatePaymentCommand(
                amount=Decimal("200.00"),
                currency=Currency.RUB,
                description="Order",
                idempotency_key="key-1",
                webhook_url="https://example.com/webhook",
                metadata={},
            ),
        )


@requires_pg
async def test_get_payment_returns_details(
    container: AsyncContainer,
) -> None:
    async with container() as ctx:
        create_handler = await ctx.get(CreatePaymentHandler)
        get_handler = await ctx.get(GetPaymentHandler)

    create_result = await create_handler(
        CreatePaymentCommand(
            amount=Decimal("50.00"),
            currency=Currency.USD,
            description="Test",
            idempotency_key="key-get",
            webhook_url="https://example.com/webhook",
            metadata={"k": "v"},
        ),
    )

    result = await get_handler(GetPaymentCommand(payment_id=create_result.payment_id))

    assert result.id == create_result.payment_id
    assert result.amount == Decimal("50.00")
    assert result.currency == Currency.USD
    assert result.status == PaymentStatus.PENDING
    assert result.metadata == {"k": "v"}


@requires_pg
async def test_get_payment_not_found_raises(
    container: AsyncContainer,
) -> None:
    async with container() as ctx:
        handler = await ctx.get(GetPaymentHandler)

    with pytest.raises(NoResultFound):
        await handler(
            GetPaymentCommand(
                payment_id=PaymentId(UUID("00000000-0000-0000-0000-000000000000")),
            ),
        )
