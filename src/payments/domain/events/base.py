"""Domain event base class."""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Self

from payments.domain.entities.base import Entity


@dataclass(frozen=True, kw_only=True, slots=True)
class Event[T: Entity[Any]]:
    """Base class for domain events."""

    @abstractmethod
    def of(self, entity: T) -> Self:
        """Create an event from the given entity."""
        raise NotImplementedError
