"""Update payment status use case."""

from dataclasses import dataclass

from payments.application.ports.clock import Clock
from payments.application.ports.payment_gateway import PaymentGateway
from payments.application.ports.transaction_manager import TransactionManager
from payments.application.ports.webhook_client import WebhookClient
from payments.domain.entities.payment_id import PaymentId
from payments.domain.value_objects.payment_status import PaymentStatus


@dataclass(frozen=True, kw_only=True, slots=True)
class UpdatePaymentStatusCommand:
    """Command to update a payment's status after processing."""

    payment_id: PaymentId
    status: PaymentStatus


class UpdatePaymentStatusHandler:
    """Updates payment status and sends webhook notification."""

    def __init__(
        self,
        payment_gateway: PaymentGateway,
        webhook_client: WebhookClient,
        clock: Clock,
        transaction_manager: TransactionManager,
    ) -> None:
        """Initialize the handler with required dependencies.

        Args:
            payment_gateway: Gateway for loading and saving payments.
            webhook_client: Client for sending webhook notifications.
            clock: Clock for obtaining the current time.
            transaction_manager: Transaction manager for committing changes.

        """
        self._payment_gateway = payment_gateway
        self._webhook_client = webhook_client
        self._clock = clock
        self._transaction_manager = transaction_manager

    async def __call__(self, command: UpdatePaymentStatusCommand) -> None:
        """Process the status update command.

        Status update is committed immediately — webhook failure
        causes a retry, but the status is already persisted.

        Args:
            command: The update payment status command.

        """
        payment = await self._payment_gateway.get_by_id(command.payment_id)

        if payment.status == PaymentStatus.PENDING:
            if command.status == PaymentStatus.SUCCEEDED:
                payment.mark_succeeded(self._clock.now())
            else:
                payment.mark_failed(self._clock.now())

        await self._transaction_manager.commit()

        await self._webhook_client.send(
            payment.webhook_url,
            {
                "payment_id": str(payment.oid),
                "status": str(payment.status),
                "amount": str(payment.amount),
                "currency": str(payment.currency),
            },
        )
