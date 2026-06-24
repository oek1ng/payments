"""Clock port for obtaining current time."""

from abc import abstractmethod
from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Abstract clock for obtaining the current time."""

    @abstractmethod
    def now(self) -> datetime:
        """Return the current datetime."""
        raise NotImplementedError
