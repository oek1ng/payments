from abc import abstractmethod
from typing import Any, Protocol

from payments.domain.events.base import Event


class EventCollector(Protocol):

    @abstractmethod
    def add(self, *events: Event) -> None:
        raise NotImplementedError

    @abstractmethod
    def collect(self) -> list[Event[Any]]:
        raise NotImplementedError
