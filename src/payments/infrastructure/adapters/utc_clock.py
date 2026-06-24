from datetime import UTC, datetime

from payments.application.ports.clock import Clock


class UTCClock(Clock):

    def now(self) -> datetime:
        return datetime.now(UTC)
