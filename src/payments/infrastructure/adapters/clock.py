"""UTC clock adapter."""

from datetime import UTC, datetime

from payments.application.ports.clock import Clock


class UTCClock(Clock):
    """UTC-based implementation of the Clock port."""

    def now(self) -> datetime:
        """Return the current datetime in UTC.

        Returns:
            The current UTC datetime.

        """
        return datetime.now(UTC)
