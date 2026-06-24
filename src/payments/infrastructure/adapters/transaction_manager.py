"""SQLAlchemy transaction manager adapter."""

from sqlalchemy.ext.asyncio import AsyncSession

from payments.application.ports.transaction_manager import TransactionManager


class SATrsansactionManager(TransactionManager):
    """SQLAlchemy implementation of the transaction manager."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the manager with an async SQLAlchemy session."""
        self._session = session

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()
