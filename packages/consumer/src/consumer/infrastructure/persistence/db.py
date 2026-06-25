"""SQLite database initialization and outbox storage."""

import json
import logging
from datetime import UTC, datetime
from uuid import uuid4

import aiosqlite

from consumer.main.config import DatabaseSettings

logger = logging.getLogger(__name__)

INIT_DDL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS processed_events (
    payment_id TEXT PRIMARY KEY,
    processed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS consumer_outbox (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_outbox_status
    ON consumer_outbox(status, created_at);
"""


async def init_db(settings: DatabaseSettings) -> aiosqlite.Connection:
    """Initialize the SQLite database and tables.

    Args:
        settings: Database configuration.

    Returns:
        An open aiosqlite connection.

    """
    db = await aiosqlite.connect(settings.path)
    db.row_factory = aiosqlite.Row
    await db.executescript(INIT_DDL)
    await db.commit()
    logger.info("SQLite database initialized", extra={"path": settings.path})
    return db


class SQLiteOutboxStore:
    """SQLite-backed storage for dedup checks and outbox CRUD."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        """Initialize the store.

        Args:
            db: Open aiosqlite connection.

        """
        self._db = db

    async def is_already_processed(self, payment_id: str) -> bool:
        """Check if a payment has already been processed.

        Args:
            payment_id: Payment ID to check.

        Returns:
            True if the event was already processed.

        """
        cursor = await self._db.execute(
            "SELECT 1 FROM processed_events WHERE payment_id = ?",
            (payment_id,),
        )
        row = await cursor.fetchone()
        return row is not None

    async def insert_processed_event(self, payment_id: str) -> None:
        """Record a processed event for deduplication.

        Args:
            payment_id: Payment ID to mark as processed.

        """
        await self._db.execute(
            "INSERT INTO processed_events (payment_id) VALUES (?)",
            (payment_id,),
        )

    async def insert_outbox_event(self, payment_id: str, status: str) -> None:
        """Insert a pending outbox event.

        Args:
            payment_id: Payment ID.
            status: Processing result ("succeeded" or "failed").

        """
        event_id = str(uuid4())
        payload = json.dumps({"payment_id": payment_id, "status": status})
        await self._db.execute(
            "INSERT INTO consumer_outbox (id, event_type, payload) VALUES (?, ?, ?)",
            (event_id, "PaymentProcessed", payload),
        )

    async def fetch_pending_events(
        self,
        batch_size: int,
        retry_base_seconds: int,
    ) -> list[dict[str, object]]:
        """Fetch pending outbox events ready for delivery.

        Args:
            batch_size: Maximum number of events to fetch.
            retry_base_seconds: Base backoff in seconds.

        Returns:
            List of pending outbox rows as dicts.

        """
        now = datetime.now(tz=UTC).isoformat()
        cursor = await self._db.execute(
            """
            SELECT * FROM consumer_outbox
            WHERE status = 'pending'
              AND (
                last_attempt_at IS NULL
                OR datetime(last_attempt_at, '+' || (? << attempts - 1) || ' seconds') <= ?
              )
            ORDER BY created_at
            LIMIT ?
            """,
            (retry_base_seconds, now, batch_size),
        )
        rows = await cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        return [dict(zip(column_names, row, strict=False)) for row in rows]

    async def mark_outbox_published(self, event_id: str) -> None:
        """Mark an outbox event as published.

        Args:
            event_id: Outbox event ID.

        """
        now = datetime.now(tz=UTC).isoformat()
        await self._db.execute(
            "UPDATE consumer_outbox SET status = 'published', last_attempt_at = ? WHERE id = ?",
            (now, event_id),
        )

    async def record_outbox_failure(self, event_id: str, current_attempts: int) -> None:
        """Increment attempt counter and update last_attempt_at.

        Args:
            event_id: Outbox event ID.
            current_attempts: Current attempt count.

        """
        now = datetime.now(tz=UTC).isoformat()
        new_attempts = current_attempts + 1
        await self._db.execute(
            "UPDATE consumer_outbox SET attempts = ?, last_attempt_at = ? WHERE id = ?",
            (new_attempts, now, event_id),
        )
