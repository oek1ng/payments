"""Application-level exceptions."""


class ApplicationError(Exception):
    """Base application error with a user-readable message."""

    def __init__(self, message: str) -> None:
        """Initialize the error.

        Args:
            message: Human-readable error message.

        """
        self.message = message
        super().__init__(message)


class WebhookError(ApplicationError):
    """Raised when a webhook delivery fails after exhausting retries."""


class IdempotencyKeyConflictError(ApplicationError):
    """Raised when an idempotent request arrives with different parameters."""

    def __init__(self, key: str) -> None:
        """Initialize the error.

        Args:
            key: The idempotency key that caused the conflict.

        """
        super().__init__(
            f"Payment with idempotency key {key} already exists with different parameters",
        )
