"""Root test fixtures — real PostgreSQL with session-scoped isolation."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock

import pytest
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from payments.main.bootstrap import setup_json, setup_map_tables
from payments.main.config import get_settings

# ── PostgreSQL availability ──────────────────────────────────────────────


def _is_postgres_available() -> bool:
    try:
        settings = get_settings()
        url = settings.postgres.uri
        loop = asyncio.new_event_loop()
        try:
            async def _test() -> None:
                engine = create_async_engine(url)
                async with engine.connect() as conn:
                    await conn.close()
                await engine.dispose()
            loop.run_until_complete(_test())
        finally:
            loop.close()
    except Exception:  # noqa: BLE001
        return False
    return True


pg_available = _is_postgres_available()
requires_pg = pytest.mark.skipif(not pg_available, reason="PostgreSQL is not available")


def _ensure_pg() -> None:
    if not pg_available:
        pytest.skip("PostgreSQL is not available")


@pytest.fixture(scope="session")
def _alembic_upgrade() -> None:
    _ensure_pg()
    setup_map_tables()
    setup_json()
    config = AlembicConfig("alembic.ini")
    alembic_command.upgrade(config, "head")


@pytest.fixture(scope="session")
async def pg_engine(_alembic_upgrade: None) -> AsyncGenerator[AsyncEngine]:
    _ensure_pg()
    settings = get_settings()
    engine = create_async_engine(settings.postgres.uri)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def session_maker(pg_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=pg_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
async def session(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, Any]:
    async with session_maker() as s:
        s.commit = AsyncMock(side_effect=s.flush)  # type: ignore[method-assign]
        yield s
        await s.rollback()
