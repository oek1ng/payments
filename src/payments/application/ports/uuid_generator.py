"""UUID generator port for generating unique identifiers."""

from abc import abstractmethod
from typing import Protocol
from uuid import UUID


class UUIDGenerator(Protocol):
    """Abstract UUID generator."""

    @abstractmethod
    def __call__(self) -> UUID:
        """Generate a new UUID."""
        raise NotImplementedError
