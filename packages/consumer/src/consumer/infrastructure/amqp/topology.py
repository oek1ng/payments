"""RabbitMQ exchanges and queues for the consumer."""

from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue

PAYMENTS_EXCHANGE = RabbitExchange(
    "payments",
    type=ExchangeType.DIRECT,
    durable=True,
)
"""Exchange where events are published."""

PAYMENTS_DLX = RabbitExchange(
    "payments.dlx",
    type=ExchangeType.DIRECT,
    durable=True,
)
"""Dead-letter exchange for failed message deliveries."""

PAYMENTS_NEW_QUEUE = RabbitQueue(
    "payments.new",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.dlx",
        "x-dead-letter-routing-key": "payments.dlq",
    },
)
"""Queue for new payment events — consumed by the consumer."""

PAYMENTS_DLQ = RabbitQueue(
    "payments.dlq",
    durable=True,
)
"""Dead-letter queue for failed payments.new deliveries."""
