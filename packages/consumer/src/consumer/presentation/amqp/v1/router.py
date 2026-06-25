"""AMQP router and subscriber handlers for the consumer."""

import logging
from typing import Any

from dishka import FromDishka
from dishka_faststream import inject
from faststream import AckPolicy
from faststream.rabbit import RabbitMessage, RabbitRouter
from pydantic import ValidationError

from consumer.application.process_payment import AlreadyProcessedError, ProcessPaymentHandler
from consumer.infrastructure.amqp.topology import (
    PAYMENTS_DLQ,
    PAYMENTS_EXCHANGE,
    PAYMENTS_NEW_QUEUE,
)
from consumer.presentation.amqp.v1.schemas import PaymentCreatedSchema

logger = logging.getLogger(__name__)

router = RabbitRouter()

payments_new_subscriber = router.subscriber(
    PAYMENTS_NEW_QUEUE,
    PAYMENTS_EXCHANGE,
    ack_policy=AckPolicy.MANUAL,
)


@payments_new_subscriber
@inject
async def on_payment_created(
    body: dict[str, Any],
    message: RabbitMessage,
    handler: FromDishka[ProcessPaymentHandler],
) -> None:
    """Handle an incoming payments.new message.

    Validates the message, then delegates to the handler
    which performs dedup, processing, and outbox writes.

    """
    try:
        event = PaymentCreatedSchema.model_validate(body)
    except ValidationError:
        logger.warning(
            "Invalid payments.new message rejected",
            extra={"body": body},
        )
        await message.reject(requeue=False)
        return

    try:
        await handler(event.id)
    except AlreadyProcessedError as exc:
        logger.debug("Duplicate payment skipped", extra={"payment_id": exc.payment_id})

    await message.ack()


dlq_subscriber = router.subscriber(queue=PAYMENTS_DLQ)


@dlq_subscriber
async def on_dead_letter(body: dict[str, object], message: RabbitMessage) -> None:
    """Log dead-lettered messages and acknowledge them."""
    logger.error("Dead-lettered payments.new message", extra={"body": body})
    await message.ack()
