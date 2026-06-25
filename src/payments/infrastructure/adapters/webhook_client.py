"""HTTP-based webhook client with exponential backoff retry."""

import asyncio
import logging
from typing import Any

import httpx

from payments.application.common.errors import WebhookError
from payments.application.ports.webhook_client import WebhookClient

logger = logging.getLogger(__name__)


class HttpxWebhookClient(WebhookClient):
    """Sends webhook notifications via HTTP with retry logic."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        max_retries: int = 3,
        base_backoff: float = 1.0,
    ) -> None:
        """Initialize the webhook client.

        Args:
            client: Configured httpx async client.
            max_retries: Maximum number of delivery attempts.
            base_backoff: Base backoff in seconds (doubles each retry).

        """
        self._client = client
        self._max_retries = max_retries
        self._base_backoff = base_backoff

    async def send(self, url: str, payload: dict[str, Any]) -> None:
        """Send a webhook notification with retries.

        Args:
            url: Target webhook URL.
            payload: JSON-serializable payload.

        Raises:
            WebhookError: If delivery fails after all retries.

        """
        for attempt in range(self._max_retries):
            try:
                response = await self._client.post(url, json=payload, timeout=10)
                response.raise_for_status()
            except Exception as exc:
                if attempt == self._max_retries - 1:
                    msg = f"Webhook delivery failed after {self._max_retries} attempts: {exc}"
                    raise WebhookError(msg) from exc
                backoff = self._base_backoff * (2**attempt)
                logger.warning(
                    "Webhook delivery attempt %d/%d failed, retrying in %.1fs",
                    attempt + 1,
                    self._max_retries,
                    backoff,
                    extra={"url": url, "error": str(exc)},
                )
                await asyncio.sleep(backoff)
            else:
                logger.debug(
                    "Webhook delivered",
                    extra={"url": url, "status": response.status_code},
                )
                return
