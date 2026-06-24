from abc import abstractmethod
from typing import Any, Protocol


class Handler(Protocol):

    @abstractmethod
    async def __call__(self, command: Any) -> Any:
        raise NotImplementedError
