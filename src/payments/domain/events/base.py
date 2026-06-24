
from abc import abstractmethod
from dataclasses import dataclass
from typing import Self

from payments.domain.entities.base import Entity


@dataclass(frozen=True, kw_only=True, slots=True)
class Event[T: Entity]:

    @abstractmethod
    def of(cls, entity: T) -> Self:
        raise NotImplementedError
