"""Outbox SQLAlchemy table definition."""

from enum import StrEnum, auto

from sqlalchemy import Column, DateTime, Enum, Integer, Table, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from payments.infrastructure.persistence.registry import metadata


class OutboxStatus(StrEnum):
    """Delivery statuses for outbox entries."""

    PENDING = auto()
    PUBLISHED = auto()
    DEAD = auto()


outbox_table = Table(
    "outbox",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("event_type", Text, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column(
        "status",
        Enum(
            OutboxStatus,
            name="outbox_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    ),
    Column("attempts", Integer, nullable=False, default=0, server_default="0"),
    Column("last_attempt_at", DateTime(timezone=True), nullable=True),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    ),
)
