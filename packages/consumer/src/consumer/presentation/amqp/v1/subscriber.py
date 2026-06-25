"""FastStream subscriber for payments.new messages."""

import logging
from typing import Any

from dishka import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitMessage
from pydantic import ValidationError

from consumer.application.process_payment import AlreadyProcessedError, ProcessPaymentHandler
from consumer.presentation.amqp.v1.router import payments_new_subscriber
from consumer.presentation.amqp.v1.schemas import PaymentCreatedSchema

logger = logging.getLogger(__name__)


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
        await handler(event.payment_id)
    except AlreadyProcessedError as exc:
        logger.debug("Duplicate payment skipped", extra={"payment_id": exc.payment_id})

    await message.ack()
