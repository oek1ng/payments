"""Payment identifier value type."""

from typing import NewType
from uuid import UUID

PaymentId = NewType("PaymentId", UUID)
