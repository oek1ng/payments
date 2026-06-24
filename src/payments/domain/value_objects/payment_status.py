from enum import StrEnum, auto


class PaymentStatus(StrEnum):
    PENDING = auto()
    SUCCEEDED = auto()
    FAILED = auto()
