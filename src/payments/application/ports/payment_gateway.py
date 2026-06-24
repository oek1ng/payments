"""Payment gateway port for persisting and retrieving payments."""

from abc import abstractmethod
from typing import Protocol

from payments.domain.entities.payment import Payment
from payments.domain.entities.payment_id import PaymentId


class PaymentGateway(Protocol):
    """Abstract payment gateway for persisting and retrieving payments."""

    @abstractmethod
    def add(self, payment: Payment) -> None:
        """Add a new payment to the gateway."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, payment_id: PaymentId) -> Payment:
        """Retrieve a payment by its ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        """Retrieve a payment by its idempotency key."""
        raise NotImplementedError
