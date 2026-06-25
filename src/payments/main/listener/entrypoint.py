"""API listener entrypoint — subscribes to payments.processed and handles results."""

import logging

import httpx
from dishka import Provider, Scope, provide
from dishka_faststream import setup_dishka
from faststream import FastStream
from faststream.rabbit import RabbitBroker

from payments.application.ports.webhook_client import WebhookClient
from payments.application.update_payment_status import UpdatePaymentStatusHandler
from payments.infrastructure.adapters.webhook_client import HttpxWebhookClient
from payments.main.bootstrap import setup_json, setup_map_tables
from payments.main.config import get_settings
from payments.main.di import create_container
from payments.presentation.api.amqp.v1.router import router

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


class ListenerHandlerProvider(Provider):
    """Handler provider specific to the API listener."""

    scope = Scope.REQUEST

    webhook_client = provide(lambda c: c, provides=WebhookClient)  # Provided via context
    handler = provide(UpdatePaymentStatusHandler)


async def run_listener() -> None:
    """Create and run the API listener (blocking)."""
    settings = get_settings()
    setup_map_tables()
    setup_json()

    broker = RabbitBroker(settings.rabbit.url)
    broker.include_router(router)
    app = FastStream(broker)

    async with httpx.AsyncClient() as http_client:
        webhook_client = HttpxWebhookClient(http_client, max_retries=3, base_backoff=1.0)
        container = create_container(
            ListenerHandlerProvider(),
            extra_context={WebhookClient: webhook_client},
        )
        setup_dishka(container, app)

        await app.run()

    await container.close()
