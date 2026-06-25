"""Webhook client port for sending HTTP notifications."""

from abc import abstractmethod
from typing import Any, Protocol


class WebhookClient(Protocol):
    """Abstract webhook client for notifying external systems."""

    @abstractmethod
    async def send(self, url: str, payload: dict[str, Any]) -> None:
        """Send a webhook notification to the given URL.

        Args:
            url: Target webhook URL.
            payload: JSON-serializable payload.

        Raises:
            WebhookError: If delivery fails after all retries.

        """
        raise NotImplementedError
