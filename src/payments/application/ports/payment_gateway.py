from abc import abstractmethod
from typing import Protocol

from payments.domain.entities.payment import Payment, PaymentId


class PaymentGateway(Protocol):

    @abstractmethod
    def add(self, payment: Payment) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, payment_id: PaymentId) -> Payment:
        raise NotImplementedError
