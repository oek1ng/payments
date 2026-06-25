"""Outbox relay entrypoint — polls outbox and publishes to RabbitMQ."""

import logging

from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from payments.infrastructure.adapters.clock import UTCClock
from payments.infrastructure.adapters.outbox_relay import OutboxRelay
from payments.infrastructure.amqp import PAYMENTS_EXCHANGE, FSRabbitPublisher
from payments.main.bootstrap import setup_json, setup_map_tables
from payments.main.config import get_settings

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


async def run_relay() -> None:
    """Create and run the outbox relay (blocking)."""
    settings = get_settings()
    setup_map_tables()
    setup_json()

    engine = create_async_engine(settings.postgres.uri)
    session_factory = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)

    async with RabbitBroker(settings.rabbit.url) as broker:
        publisher = FSRabbitPublisher(broker, PAYMENTS_EXCHANGE)
        relay = OutboxRelay(
            session_factory=session_factory,
            publisher=publisher,
            clock=UTCClock(),
            settings=settings.outbox,
        )
        await relay.run()

    await engine.dispose()
