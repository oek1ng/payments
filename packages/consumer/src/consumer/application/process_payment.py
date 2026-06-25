"""Process payment handler — emulates payment processing with deduplication."""

import asyncio
import logging
import random
from uuid import UUID

from consumer.application.ports.outbox_store import OutboxStore
from consumer.application.ports.transaction_manager import TransactionManager
from consumer.main.config import ProcessingSettings

logger = logging.getLogger(__name__)


class AlreadyProcessedError(Exception):
    """Raised when a payment has already been processed."""

    def __init__(self, payment_id: str) -> None:
        """Initialize the error.

        Args:
            payment_id: The payment ID that was already processed.

        """
        super().__init__(f"Payment {payment_id} already processed")
        self.payment_id = payment_id


class ProcessPaymentHandler:
    """Emulates payment processing, handles dedup and outbox writes."""

    def __init__(
        self,
        settings: ProcessingSettings,
        store: OutboxStore,
        transaction_manager: TransactionManager,
    ) -> None:
        """Initialize the handler.

        Args:
            settings: Processing emulation settings.
            store: Outbox store for dedup and outbox writes.
            transaction_manager: Transaction manager for committing.

        """
        self._settings = settings
        self._store = store
        self._transaction_manager = transaction_manager

    async def __call__(self, payment_id: UUID) -> str:
        """Process a payment: dedup check, emulate, write outbox.

        Args:
            payment_id: ID of the payment to process.

        Returns:
            "succeeded" or "failed".

        Raises:
            AlreadyProcessedError: If the payment was already processed.

        """
        payment_id_str = str(payment_id)

        if await self._store.is_already_processed(payment_id_str):
            raise AlreadyProcessedError(payment_id_str)

        result = await self._emulate(payment_id)

        await self._transaction_manager.begin()
        try:
            await self._store.insert_processed_event(payment_id_str)
            await self._store.insert_outbox_event(payment_id_str, result)
            await self._transaction_manager.commit()
        except Exception:
            await self._transaction_manager.rollback()
            raise

        return result

    async def _emulate(self, payment_id: UUID) -> str:
        """Emulate external payment gateway processing.

        Args:
            payment_id: ID of the payment.

        Returns:
            "succeeded" or "failed".

        """
        delay = random.uniform(  # noqa: S311
            self._settings.min_delay_seconds,
            self._settings.max_delay_seconds,
        )
        logger.info(
            "Processing payment",
            extra={"payment_id": str(payment_id), "delay": f"{delay:.1f}s"},
        )
        await asyncio.sleep(delay)

        success = random.random() < self._settings.success_probability  # noqa: S311
        result = "succeeded" if success else "failed"
        logger.info(
            "Payment processed",
            extra={"payment_id": str(payment_id), "result": result},
        )
        return result
