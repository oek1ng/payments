"""Consumer entrypoint — subscribes to payments.new and processes payments."""

import asyncio
import logging

from dishka.integrations.faststream import setup_dishka
from faststream import FastStream
from faststream.rabbit import RabbitBroker

from consumer.infrastructure.persistence.db import init_db
from consumer.main.config import get_settings
from consumer.main.di import create_container
from consumer.presentation.amqp.v1.router import router

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    """Start the consumer subscriber."""
    settings = get_settings()

    await init_db(settings.database)

    broker = RabbitBroker(settings.rabbit.url)
    broker.include_router(router)

    app = FastStream(broker)
    container = create_container()
    setup_dishka(container, app)

    await app.run()
    await container.close()


if __name__ == "__main__":
    asyncio.run(main())
