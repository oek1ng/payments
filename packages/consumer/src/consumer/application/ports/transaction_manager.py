"""Transaction manager port for managing database transactions."""

from abc import abstractmethod
from typing import Protocol


class TransactionManager(Protocol):
    """Abstract transaction manager for managing database transactions."""

    @abstractmethod
    async def begin(self) -> None:
        """Begin a new transaction."""
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        raise NotImplementedError
