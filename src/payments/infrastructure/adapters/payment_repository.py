"""SQLAlchemy payment repository adapter."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from payments.application.ports.payment_gateway import PaymentGateway
from payments.domain.entities.payment import Payment, PaymentId
from payments.infrastructure.persistence.tables.payments import payments_table


class SqlAlchemyPaymentRepository(PaymentGateway):
    """SQLAlchemy implementation of the payment repository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async SQLAlchemy session."""
        self._session = session

    async def get(self, payment_id: PaymentId) -> Payment:
        """Retrieve a payment by its ID.

        Returns:
            The matching payment entity.

        """
        stmt = select(Payment).where(payments_table.c.id == payment_id)
        result = await self._session.execute(stmt)

        return result.scalar_one()
