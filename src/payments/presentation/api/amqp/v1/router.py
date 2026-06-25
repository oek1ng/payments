"""FastStream subscriber for payments.processed messages."""

import logging
from typing import Any

from dishka import FromDishka
from dishka_faststream import inject
from faststream import AckPolicy
from faststream.rabbit import RabbitMessage, RabbitRouter
from pydantic import ValidationError

from payments.application.common.errors import WebhookError
from payments.application.update_payment_status import (
    UpdatePaymentStatusCommand,
    UpdatePaymentStatusHandler,
)
from payments.domain.entities.payment_id import PaymentId
from payments.infrastructure.amqp import (
    PAYMENTS_EXCHANGE,
    PAYMENTS_PROCESSED_DLQ,
    PAYMENTS_PROCESSED_QUEUE,
)
from payments.presentation.api.amqp.v1.schemas import PaymentProcessedSchema

logger = logging.getLogger(__name__)

router = RabbitRouter()

payments_processed_subscriber = router.subscriber(
    PAYMENTS_PROCESSED_QUEUE,
    PAYMENTS_EXCHANGE,
    ack_policy=AckPolicy.MANUAL,
)


@payments_processed_subscriber
@inject
async def on_payment_processed(
    body: dict[str, Any],
    message: RabbitMessage,
    handler: FromDishka[UpdatePaymentStatusHandler],
) -> None:
    """Handle an incoming payments.processed message.

    Validates the message, updates payment status, sends webhook.

    Args:
        body: Raw message body dict.
        message: RabbitMQ message for ack/reject control.
        handler: Injected update payment status handler.

    """
    try:
        event = PaymentProcessedSchema.model_validate(body)
    except ValidationError:
        logger.warning(
            "Invalid payments.processed message rejected",
            extra={"body": body},
        )
        await message.reject(requeue=False)
        return

    command = UpdatePaymentStatusCommand(
        payment_id=PaymentId(event.payment_id),
        status=event.status,
    )
    try:
        await handler(command)
    except WebhookError:
        logger.exception("Webhook delivery failed, payment status already updated")
    await message.ack()


dlq_subscriber = router.subscriber(queue=PAYMENTS_PROCESSED_DLQ)


@dlq_subscriber
async def on_dead_letter(
    body: dict[str, object],
    message: RabbitMessage,
) -> None:
    """Log dead-lettered messages and acknowledge them."""
    logger.error("Dead-lettered payments.processed message", extra={"body": body})
    await message.ack()
