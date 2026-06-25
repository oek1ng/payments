"""Consumer relay entrypoint — polls consumer_outbox and publishes to payments.processed."""

import logging

import aiosqlite
from faststream.rabbit import RabbitBroker

from consumer.infrastructure.adapters.relay import ConsumerOutboxRelay
from consumer.infrastructure.amqp import PAYMENTS_EXCHANGE, FSRabbitPublisher
from consumer.infrastructure.persistence.db import init_db
from consumer.main.config import get_settings

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


async def run_relay() -> None:
    """Create and run the consumer outbox relay (blocking)."""
    settings = get_settings()

    await init_db(settings.database)

    async with RabbitBroker(settings.rabbit.url) as broker:
        publisher = FSRabbitPublisher(broker, PAYMENTS_EXCHANGE)
        relay = ConsumerOutboxRelay(
            db_factory=aiosqlite.connect,
            db_path=settings.database.path,
            publisher=publisher,
            settings=settings.outbox,
        )
        await relay.run()
