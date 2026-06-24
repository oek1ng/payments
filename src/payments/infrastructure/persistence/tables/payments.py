"""Payments SQLAlchemy table definition."""

from sqlalchemy import Column, DateTime, Enum, Numeric, Table, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from payments.domain.entities.payment import Payment
from payments.domain.value_objects.currency import Currency
from payments.domain.value_objects.payment_status import PaymentStatus
from payments.infrastructure.persistence.registry import mapper_registry, metadata

payments_table = Table(
    "payments",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("amount", Numeric(precision=10, scale=2, asdecimal=True), nullable=False),
    Column(
        "currency",
        Enum(
            Currency,
            name="payment_currency",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    ),
    Column("description", Text, nullable=False),
    Column("idempotency_key", Text, nullable=False, unique=True),
    Column("webhook_url", Text, nullable=False),
    Column("metadata", JSONB, nullable=False),
    Column(
        "status",
        Enum(
            PaymentStatus,
            name="payment_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
)


def map_payments_table() -> None:
    """Map the Payment entity to the payments SQLAlchemy table."""
    mapper_registry.map_imperatively(
        Payment,
        payments_table,
        properties={
            "oid": payments_table.c.id,
        },
    )
