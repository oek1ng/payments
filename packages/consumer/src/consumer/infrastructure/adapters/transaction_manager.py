"""SQLite transaction manager adapter."""

import aiosqlite


class SQLiteTransactionManager:
    """Manages SQLite transactions via aiosqlite."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        """Initialize the transaction manager.

        Args:
            db: Open aiosqlite connection.

        """
        self._db = db

    async def begin(self) -> None:
        """Begin an immediate transaction."""
        await self._db.execute("BEGIN IMMEDIATE")

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._db.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self._db.rollback()
