"""Event publisher port for publishing domain events."""

from abc import abstractmethod
from typing import Any, Protocol, Self

from payments.domain.events.base import Event


class EventPublisher(Protocol):
    """Abstract event publisher for publishing domain events."""

    @abstractmethod
    async def publish(self, *events: Event[Any]) -> Self:
        """Publish domain events asynchronously."""
        raise NotImplementedError
