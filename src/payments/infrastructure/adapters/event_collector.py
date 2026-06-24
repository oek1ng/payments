from typing import Any

from payments.application.ports.event_collector import EventCollector
from payments.domain.events.base import Event


class InMemoryEventCollector(EventCollector):

    def __init__(self) -> None:
        self._events = []

    def add(self, *events: Event) -> None:
        self._events.extend(events)

    def collect(self) -> list[Event[Any]]:
        return self._events
