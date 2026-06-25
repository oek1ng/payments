from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from payments.presentation.api.amqp.v1.schemas import PaymentProcessedSchema
from payments.presentation.api.http.v1.schemas import CreatePaymentRequest


def test_validate_minimal_create_payment_request() -> None:
    request = CreatePaymentRequest.model_validate({
        "amount": "100.00",
        "currency": "rub",
        "description": "Order #42",
        "webhook_url": "https://example.com/webhook",
    })

    assert request.amount == Decimal("100.00")
    assert request.currency == "rub"
    assert request.metadata == {}


def test_validate_create_payment_with_metadata() -> None:
    request = CreatePaymentRequest.model_validate({
        "amount": "50.00",
        "currency": "usd",
        "description": "Order #43",
        "webhook_url": "https://example.com/webhook",
        "metadata": {"order_id": 42},
    })

    assert request.metadata == {"order_id": 42}


def test_create_payment_rejects_negative_amount() -> None:
    with pytest.raises(ValidationError):
        CreatePaymentRequest.model_validate({
            "amount": "-1.00",
            "currency": "rub",
            "description": "Invalid",
            "webhook_url": "https://example.com/webhook",
        })


def test_create_payment_rejects_invalid_currency() -> None:
    with pytest.raises(ValidationError):
        CreatePaymentRequest.model_validate({
            "amount": "100.00",
            "currency": "GBP",
            "description": "Invalid",
            "webhook_url": "https://example.com/webhook",
        })


def test_validate_payment_processed_schema() -> None:
    payment_id = uuid4()
    event = PaymentProcessedSchema.model_validate({
        "payment_id": str(payment_id),
        "status": "succeeded",
    })

    assert event.payment_id == payment_id
    assert event.status == "succeeded"


def test_payment_processed_schema_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        PaymentProcessedSchema.model_validate({
            "payment_id": str(uuid4()),
            "status": "unknown",
        })
