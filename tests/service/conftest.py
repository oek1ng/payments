"""Service test fixtures using real DI container and test DB session."""

from collections.abc import AsyncGenerator

import httpx
import pytest
from dishka import AsyncContainer, Provider, Scope, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from payments.main.bootstrap import (
    setup_http_middlewares,
    setup_http_routes,
)
from payments.main.config import AppSettings, OutboxSettings, PostgresSettings, RabbitSettings
from payments.main.di import create_container
from payments.presentation.api.http.v1.error_handlers import setup_http_error_handlers

TEST_API_KEY = "test-api-key"


class _TestSessionProvider(Provider):
    scope = Scope.REQUEST

    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self._session = session

    @provide
    async def session(self) -> AsyncSession:
        return self._session


class TestSettings:
    def __init__(self) -> None:
        self.app = AppSettings(api_key=TEST_API_KEY)


@pytest.fixture
async def container(session: AsyncSession) -> AsyncGenerator[AsyncContainer]:
    c = create_container(
        _TestSessionProvider(session),
        extra_context={
            AppSettings: AppSettings(api_key=TEST_API_KEY),
            PostgresSettings: PostgresSettings(),
            RabbitSettings: RabbitSettings(),
            OutboxSettings: OutboxSettings(),
        },
    )
    yield c
    await c.close()


@pytest.fixture
def app(container: AsyncContainer) -> FastAPI:
    app_instance = FastAPI(title="Payments Test", debug=False, version="0.1.0")
    setup_http_routes(app_instance)
    setup_dishka(container, app_instance)
    setup_http_middlewares(app_instance, settings=TestSettings())  # type: ignore[arg-type]
    setup_http_error_handlers(app_instance)
    app_instance.add_exception_handler(
        NoResultFound,
        lambda r, e: JSONResponse({"detail": "Resource not found"}, status_code=404),
    )
    return app_instance


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c
