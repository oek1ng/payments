"""Outbox store port for dedup checks and outbox persistence."""

from abc import abstractmethod
from typing import Any, Protocol


class OutboxStore(Protocol):
    """Abstract outbox store for dedup and outbox operations."""

    @abstractmethod
    async def is_already_processed(self, payment_id: str) -> bool:
        """Check if a payment has already been processed."""
        raise NotImplementedError

    @abstractmethod
    async def insert_processed_event(self, payment_id: str) -> None:
        """Record a processed event for deduplication."""
        raise NotImplementedError

    @abstractmethod
    async def insert_outbox_event(self, payment_id: str, status: str) -> None:
        """Insert a pending outbox event."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_pending_events(
        self,
        batch_size: int,
        retry_base_seconds: int,
    ) -> list[dict[str, Any]]:
        """Fetch pending outbox events ready for delivery."""
        raise NotImplementedError

    @abstractmethod
    async def mark_outbox_published(self, event_id: str) -> None:
        """Mark an outbox event as published."""
        raise NotImplementedError

    @abstractmethod
    async def record_outbox_failure(self, event_id: str, current_attempts: int) -> None:
        """Increment attempt counter and update last_attempt_at."""
        raise NotImplementedError
