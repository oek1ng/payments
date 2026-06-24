from abc import abstractmethod
from typing import Any, Protocol, Self

from payments.domain.events.base import Event


class EventPublisher(Protocol):

    @abstractmethod
    async def publish(self, *events: Event[Any]) -> Self:
        raise NotImplementedError
