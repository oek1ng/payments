"""Service tests for the payments HTTP API using real DB."""

from http import HTTPStatus
from uuid import uuid4

from httpx import AsyncClient

from tests.conftest import requires_pg


@requires_pg
async def test_create_payment_returns_202_accepted(client: AsyncClient) -> None:
    payload = {
        "amount": "125.50",
        "currency": "rub",
        "description": "Order #42",
        "metadata": {"order_id": 42},
        "webhook_url": "https://client.example/webhooks/payments",
    }

    response = await client.post(
        "/v1/payments/",
        headers={"X-API-Key": "test-api-key", "Idempotency-Key": "key-1"},
        json=payload,
    )

    assert response.status_code == HTTPStatus.ACCEPTED
    body = response.json()
    assert body["status"] == "pending"
    assert body["payment_id"] is not None
    assert body["created_at"]


@requires_pg
async def test_create_payment_requires_api_key(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/payments/",
        headers={"X-API-Key": "wrong-key", "Idempotency-Key": "key-1"},
        json={
            "amount": "1.00",
            "currency": "rub",
            "description": "Test",
            "webhook_url": "https://example.com/webhook",
        },
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED


@requires_pg
async def test_create_payment_requires_idempotency_key(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/payments/",
        headers={"X-API-Key": "test-api-key"},
        json={
            "amount": "1.00",
            "currency": "rub",
            "description": "Test",
            "webhook_url": "https://example.com/webhook",
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@requires_pg
async def test_create_payment_idempotency_returns_same_payment(client: AsyncClient) -> None:
    headers = {"X-API-Key": "test-api-key", "Idempotency-Key": "key-1"}
    payload = {
        "amount": "125.50",
        "currency": "rub",
        "description": "Order #42",
        "webhook_url": "https://client.example/webhooks/payments",
    }

    first = await client.post("/v1/payments/", headers=headers, json=payload)
    second = await client.post("/v1/payments/", headers=headers, json=payload)

    assert first.status_code == HTTPStatus.ACCEPTED
    assert second.status_code == HTTPStatus.ACCEPTED
    assert first.json()["payment_id"] == second.json()["payment_id"]


@requires_pg
async def test_create_payment_conflict_on_different_body_with_same_key(client: AsyncClient) -> None:
    headers = {"X-API-Key": "test-api-key", "Idempotency-Key": "key-1"}

    await client.post(
        "/v1/payments/",
        headers=headers,
        json={
            "amount": "125.50",
            "currency": "rub",
            "description": "Order #42",
            "webhook_url": "https://example.com/webhook",
        },
    )
    response = await client.post(
        "/v1/payments/",
        headers=headers,
        json={
            "amount": "200.00",
            "currency": "rub",
            "description": "Different",
            "webhook_url": "https://example.com/webhook",
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert "different parameters" in response.json()["detail"]


@requires_pg
async def test_get_payment_returns_payment_details(client: AsyncClient) -> None:
    headers = {"X-API-Key": "test-api-key", "Idempotency-Key": "get-detail-key"}

    create_resp = await client.post(
        "/v1/payments/",
        headers=headers,
        json={
            "amount": "50.00",
            "currency": "usd",
            "description": "Order",
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert create_resp.status_code == HTTPStatus.ACCEPTED, create_resp.text
    payment_id = create_resp.json()["payment_id"]

    response = await client.get(
        f"/v1/payments/{payment_id}",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["id"] == payment_id
    assert body["amount"] == "50.00"
    assert body["currency"] == "usd"
    assert body["status"] == "pending"


@requires_pg
async def test_get_payment_returns_404_for_unknown_payment(client: AsyncClient) -> None:
    response = await client.get(
        f"/v1/payments/{uuid4()}",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


@requires_pg
async def test_health_endpoint_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/v1/health", headers={"X-API-Key": "test-api-key"})

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}
