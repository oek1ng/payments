"""Payment gateway port for persisting and retrieving payments."""

from abc import abstractmethod
from typing import Protocol

from payments.domain.entities.payment import Payment, PaymentId


class PaymentGateway(Protocol):
    """Abstract payment gateway for persisting and retrieving payments."""

    @abstractmethod
    def add(self, payment: Payment) -> None:
        """Add a new payment to the gateway."""
        raise NotImplementedError

    @abstractmethod
    async def get(self, payment_id: PaymentId) -> Payment:
        """Retrieve a payment by its ID."""
        raise NotImplementedError
