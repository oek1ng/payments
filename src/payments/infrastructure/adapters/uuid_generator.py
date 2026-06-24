from uuid import UUID, uuid7

from payments.application.ports.uuid_generator import UUIDGenerator


class TimeBasedUUIDGenerator(UUIDGenerator):

    def __call__(self) -> UUID:
        return uuid7()
