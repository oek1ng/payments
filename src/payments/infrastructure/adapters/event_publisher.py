"""Outbox-backed event publisher adapter."""

import dataclasses
from typing import Any, Self

from sqlalchemy.ext.asyncio import AsyncSession

from payments.application.ports.event_publisher import EventPublisher
from payments.application.ports.uuid_generator import UUIDGenerator
from payments.domain.events.base import Event
from payments.infrastructure.persistence.tables.outbox import OutboxStatus, outbox_table


class OutboxEventPublisher(EventPublisher):
    """Persists events to the outbox table for later delivery."""

    def __init__(self, uuid_generator: UUIDGenerator, session: AsyncSession) -> None:
        """Initialize the publisher with the database session."""
        self._uuid_generator = uuid_generator
        self._session = session

    async def publish(self, *events: Event[Any]) -> Self:
        """Insert events into the outbox table.

        Args:
            *events: Domain events to persist.

        Returns:
            Self for chaining.

        """
        for event in events:
            stmt = outbox_table.insert().values(
                id=self._uuid_generator(),
                event_type=type(event).__name__,
                payload=dataclasses.asdict(event),
                status=OutboxStatus.PENDING,
            )
            await self._session.execute(stmt)
        return self
