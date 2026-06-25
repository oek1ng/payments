"""RabbitMQ exchanges and queues used by the payments package."""

from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue

PAYMENTS_EXCHANGE = RabbitExchange(
    "payments",
    type=ExchangeType.DIRECT,
    durable=True,
)
"""Exchange where outbox relay publishes events."""

PAYMENTS_DLX = RabbitExchange(
    "payments.dlx",
    type=ExchangeType.DIRECT,
    durable=True,
)
"""Dead-letter exchange for failed message deliveries."""

PAYMENTS_PROCESSED_QUEUE = RabbitQueue(
    "payments.processed",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.dlx",
        "x-dead-letter-routing-key": "payments.processed.dlq",
    },
)
"""Queue for processed payment results — consumed by the API listener."""

PAYMENTS_PROCESSED_DLQ = RabbitQueue(
    "payments.processed.dlq",
    durable=True,
)
"""Dead-letter queue for failed payments.processed deliveries."""
