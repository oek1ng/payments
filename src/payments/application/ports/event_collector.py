"""Event collector port for collecting domain events."""

from abc import abstractmethod
from typing import Any, Protocol

from payments.domain.events.base import Event


class EventCollector(Protocol):
    """Collects domain events for later publishing."""

    @abstractmethod
    def add(self, *events: Event[Any]) -> None:
        """Add events to the collection."""
        raise NotImplementedError

    @abstractmethod
    def collect(self) -> list[Event[Any]]:
        """Return and clear the collected events."""
        raise NotImplementedError
