"""Currency value object."""

from enum import StrEnum, auto


class Currency(StrEnum):
    """Supported currency codes."""

    RUB = auto()
    USD = auto()
    EUR = auto()
