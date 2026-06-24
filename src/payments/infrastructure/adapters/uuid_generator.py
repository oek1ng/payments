"""Time-based UUID generator adapter."""

from uuid import UUID, uuid7

from payments.application.ports.uuid_generator import UUIDGenerator


class TimeBasedUUIDGenerator(UUIDGenerator):
    """Time-based (UUIDv7) implementation of the UUID generator."""

    def __call__(self) -> UUID:
        """Generate a new UUIDv7.

        Returns:
            A new UUIDv7.

        """
        return uuid7()
