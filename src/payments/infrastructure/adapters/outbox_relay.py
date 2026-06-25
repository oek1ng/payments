"""Outbox relay — reads pending events and publishes them to RabbitMQ."""

import asyncio
import logging
from abc import abstractmethod
from datetime import datetime
from typing import Any, Protocol, TypedDict, cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from payments.application.ports.clock import Clock
from payments.infrastructure.persistence.tables.outbox import OutboxStatus, outbox_table
from payments.main.config import OutboxSettings

logger = logging.getLogger(__name__)


class MessagePublisher(Protocol):
    """Protocol for publishing messages to a message broker."""

    @abstractmethod
    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        """Publish a message with the given routing key and payload."""
        raise NotImplementedError


class OutboxRow(TypedDict):
    """Typed representation of an outbox table row."""

    id: UUID
    attempts: int
    last_attempt_at: datetime | None
    payload: dict[str, Any]


class OutboxRelay:
    """Polls the outbox table and publishes pending events to RabbitMQ."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        publisher: MessagePublisher,
        clock: Clock,
        settings: OutboxSettings,
    ) -> None:
        """Initialize the relay.

        Args:
            session_factory: Async SQLAlchemy session factory.
            publisher: Message publisher for delivering events to the broker.
            clock: Clock for obtaining the current time.
            settings: Outbox configuration.

        """
        self._session_factory = session_factory
        self._publisher = publisher
        self._clock = clock
        self._settings = settings

    async def run(self) -> None:
        """Run the relay loop with configurable polling interval."""
        logger.info(
            "Outbox relay started",
            extra={
                "batch_size": self._settings.batch_size,
                "poll_interval": self._settings.poll_interval_seconds,
                "max_attempts": self._settings.max_attempts,
            },
        )
        while True:
            try:
                async with self._session_factory() as session:
                    await self._process_batch(session)
            except Exception:
                logger.exception("Outbox relay iteration failed")
            await asyncio.sleep(self._settings.poll_interval_seconds)

    async def _process_batch(self, session: AsyncSession) -> None:
        """Fetch pending events, publish to broker, and update statuses.

        Args:
            session: Active async SQLAlchemy session.

        """
        rows = await self._fetch_pending(session)
        if not rows:
            return

        for row in rows:
            attempts: int = row["attempts"]
            last_attempt_at: datetime | None = row["last_attempt_at"]
            if not self._is_backoff_elapsed(attempts, last_attempt_at):
                continue

            event_id: UUID = row["id"]
            payload: dict[str, Any] = row["payload"]
            try:
                await self._publisher.publish("payments.new", payload)
                await self._mark_published(session, event_id)
                logger.debug("Published outbox event", extra={"event_id": str(event_id)})
            except Exception:
                logger.exception(
                    "Failed to publish outbox event",
                    extra={"event_id": str(event_id), "attempts": attempts},
                )
                await self._record_failure(session, row)

        await session.commit()

    async def _fetch_pending(self, session: AsyncSession) -> list[OutboxRow]:
        """Fetch pending outbox rows with FOR UPDATE SKIP LOCKED.

        Args:
            session: Active async SQLAlchemy session.

        Returns:
            List of pending outbox rows.

        """
        stmt = (
            select(outbox_table)
            .where(outbox_table.c.status == OutboxStatus.PENDING)
            .order_by(outbox_table.c.created_at)
            .limit(self._settings.batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        return [cast("OutboxRow", dict(row)) for row in result.mappings().all()]

    def _is_backoff_elapsed(self, attempts: int, last_attempt_at: datetime | None) -> bool:
        """Check if retry backoff has elapsed.

        Args:
            attempts: Number of previous delivery attempts.
            last_attempt_at: Timestamp of the last attempt, or None.

        Returns:
            True if the event is ready for retry.

        """
        if last_attempt_at is None:
            return True
        now = self._clock.now()
        backoff_seconds: int = self._settings.retry_base_seconds << (attempts - 1)
        elapsed: float = (now - last_attempt_at).total_seconds()
        return elapsed >= backoff_seconds

    async def _mark_published(self, session: AsyncSession, event_id: UUID) -> None:
        """Mark an outbox entry as published.

        Args:
            session: Active async SQLAlchemy session.
            event_id: UUID of the outbox entry.

        """
        stmt = (
            update(outbox_table)
            .where(outbox_table.c.id == event_id)
            .values(
                status=OutboxStatus.PUBLISHED,
                last_attempt_at=self._clock.now(),
            )
        )
        await session.execute(stmt)

    async def _record_failure(self, session: AsyncSession, row_data: OutboxRow) -> None:
        """Increment attempt counter and update last_attempt_at.

        Args:
            session: Active async SQLAlchemy session.
            row_data: Outbox row data with id and attempts fields.

        """
        new_attempts: int = row_data["attempts"] + 1
        stmt = (
            update(outbox_table)
            .where(outbox_table.c.id == row_data["id"])
            .values(
                attempts=new_attempts,
                last_attempt_at=self._clock.now(),
            )
        )
        await session.execute(stmt)
