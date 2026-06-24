"""Pydantic schemas for HTTP API request and response models."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from payments.domain.value_objects.currency import Currency
from payments.domain.value_objects.payment_status import PaymentStatus


class CreatePaymentRequest(BaseModel):
    """Request body for creating a payment."""

    amount: Decimal
    currency: Currency
    description: str
    webhook_url: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreatePaymentResponse(BaseModel):
    """Response body after creating a payment."""

    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class GetPaymentResponse(BaseModel):
    """Response body for payment details."""

    id: UUID
    amount: Decimal
    currency: Currency
    description: str
    idempotency_key: str
    webhook_url: str
    metadata: dict[str, Any]
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime
