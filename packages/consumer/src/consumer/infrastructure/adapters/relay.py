"""Consumer outbox relay — reads pending events and publishes to payments.processed."""

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

from consumer.infrastructure.adapters.transaction_manager import SQLiteTransactionManager
from consumer.infrastructure.amqp.publisher import FSRabbitPublisher
from consumer.infrastructure.persistence.db import SQLiteOutboxStore
from consumer.main.config import OutboxSettings

logger = logging.getLogger(__name__)


class ConsumerOutboxRelay:
    """Polls consumer_outbox and publishes to payments.processed."""

    def __init__(
        self,
        db_factory: Callable[..., Any],
        db_path: str,
        publisher: FSRabbitPublisher,
        settings: OutboxSettings,
    ) -> None:
        """Initialize the relay.

        Args:
            db_factory: aiosqlite.connect function.
            db_path: Path to the SQLite database.
            publisher: RabbitMQ message publisher.
            settings: Outbox configuration.

        """
        self._db_factory = db_factory
        self._db_path = db_path
        self._publisher = publisher
        self._settings = settings

    async def run(self) -> None:
        """Run the relay loop with configurable polling interval."""
        logger.info(
            "Consumer outbox relay started",
            extra={
                "batch_size": self._settings.batch_size,
                "poll_interval": self._settings.poll_interval_seconds,
            },
        )
        while True:
            try:
                async with self._db_factory(self._db_path) as db:
                    store = SQLiteOutboxStore(db)
                    tx = SQLiteTransactionManager(db)
                    await self._process_batch(store, tx)
            except Exception:
                logger.exception("Consumer outbox relay iteration failed")
            await asyncio.sleep(self._settings.poll_interval_seconds)

    async def _process_batch(self, store: SQLiteOutboxStore, tx: SQLiteTransactionManager) -> None:
        """Fetch pending events and publish to RabbitMQ."""
        rows = await store.fetch_pending_events(
            self._settings.batch_size,
            self._settings.retry_base_seconds,
        )
        if not rows:
            return

        for row in rows:
            event_id: str = row["id"]  # type: ignore[assignment]
            attempts: int = row["attempts"]  # type: ignore[assignment]
            payload_str: str = row["payload"]  # type: ignore[assignment]
            payload: dict[str, Any] = json.loads(payload_str)

            try:
                await self._publisher.publish("payments.processed", payload)
                await store.mark_outbox_published(event_id)
                logger.debug(
                    "Published consumer outbox event",
                    extra={"event_id": event_id},
                )
            except Exception:
                logger.exception(
                    "Failed to publish consumer outbox event",
                    extra={"event_id": event_id, "attempts": attempts},
                )
                await store.record_outbox_failure(event_id, attempts)

        await tx.commit()
