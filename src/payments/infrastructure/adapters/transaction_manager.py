
from sqlalchemy.ext.asyncio import AsyncSession

from payments.application.ports.transaction_manager import TransactionManager


class SATrsansactionManager(TransactionManager):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()
        