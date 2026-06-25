from payments.application.common.exceptions import (
    ApplicationError,
    IdempotencyKeyConflictError,
    WebhookError,
)


def test_application_error_has_message() -> None:
    exc = ApplicationError("test message")

    assert exc.message == "test message"
    assert str(exc) == "test message"


def test_webhook_error_inherits_application_error() -> None:
    exc = WebhookError("webhook failed")

    assert isinstance(exc, ApplicationError)
    assert exc.message == "webhook failed"


def test_idempotency_key_conflict_error_contains_key() -> None:
    exc = IdempotencyKeyConflictError("my-key")

    assert isinstance(exc, ApplicationError)
    assert "my-key" in exc.message
    assert "different parameters" in exc.message
