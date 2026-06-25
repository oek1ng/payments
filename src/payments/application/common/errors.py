"""Application-level exceptions."""


class WebhookError(Exception):
    """Raised when a webhook delivery fails after exhausting retries."""
