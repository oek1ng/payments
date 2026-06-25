"""Consumer domain schemas for AMQP messages."""

from uuid import UUID

from pydantic import BaseModel


class PaymentCreatedSchema(BaseModel):
    """Schema for the payments.new message from the outbox relay."""

    payment_id: UUID


class PaymentProcessedSchema(BaseModel):
    """Schema for the payments.processed message sent back to the API."""

    payment_id: UUID
    status: str
