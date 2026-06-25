"""RabbitMQ message schemas for the AMQP presentation layer."""

from uuid import UUID

from pydantic import BaseModel

from payments.domain.value_objects.payment_status import PaymentStatus


class PaymentProcessedSchema(BaseModel):
    """Schema for the payments.processed message from the consumer."""

    payment_id: UUID
    status: PaymentStatus
