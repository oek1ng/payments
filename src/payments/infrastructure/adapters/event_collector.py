"""In-memory event collector adapter."""

from typing import Any

from payments.application.ports.event_collector import EventCollector
from payments.domain.events.base import Event


class InMemoryEventCollector(EventCollector):
    """In-memory implementation of EventCollector."""

    def __init__(self) -> None:
        """Initialize an empty event collector."""
        self._events: list[Event[Any]] = []

    def add(self, *events: Event[Any]) -> None:
        """Add events to the in-memory collection."""
        self._events.extend(events)

    def collect(self) -> list[Event[Any]]:
        """Return and clear the collected events.

        Returns:
            The list of collected events.

        """
        events = self._events.copy()
        self._events.clear()
        return events
