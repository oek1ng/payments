"""Transaction manager port for managing database transactions."""

from abc import abstractmethod
from typing import Protocol


class TransactionManager(Protocol):
    """Abstract transaction manager for committing database transactions."""

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        raise NotImplementedError
