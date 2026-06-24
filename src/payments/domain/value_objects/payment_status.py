"""Payment status value object."""

from enum import StrEnum, auto


class PaymentStatus(StrEnum):
    """Payment lifecycle statuses."""

    PENDING = auto()
    SUCCEEDED = auto()
    FAILED = auto()
