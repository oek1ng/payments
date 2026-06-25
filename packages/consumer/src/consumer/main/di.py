"""Dependency injection container for the consumer."""

from collections.abc import AsyncIterator

import aiosqlite
from dishka import (
    AsyncContainer,
    Provider,
    Scope,
    from_context,
    make_async_container,
    provide,
)

from consumer.application.ports.outbox_store import OutboxStore
from consumer.application.ports.transaction_manager import TransactionManager
from consumer.application.process_payment import ProcessPaymentHandler
from consumer.infrastructure.adapters.transaction_manager import SQLiteTransactionManager
from consumer.infrastructure.persistence.db import SQLiteOutboxStore
from consumer.main.config import (
    AppSettings,
    DatabaseSettings,
    ProcessingSettings,
    RabbitSettings,
    get_settings,
)


class ConfigProvider(Provider):
    """Pulls configuration from the container context."""

    scope = Scope.APP

    app_settings = from_context(AppSettings)
    rabbit_settings = from_context(RabbitSettings)
    database_settings = from_context(DatabaseSettings)
    processing_settings = from_context(ProcessingSettings)


class AdapterProvider(Provider):
    """Infrastructure adapters bound to their ports."""

    scope = Scope.REQUEST

    store = provide(SQLiteOutboxStore, provides=OutboxStore)
    transaction_manager = provide(SQLiteTransactionManager, provides=TransactionManager)


class HandlerProvider(Provider):
    """Application handlers."""

    scope = Scope.REQUEST

    @provide
    def process_payment(
        self,
        settings: ProcessingSettings,
        store: OutboxStore,
        transaction_manager: TransactionManager,
    ) -> ProcessPaymentHandler:
        """Create the payment processing handler.

        Returns:
            Process payment handler.

        """
        return ProcessPaymentHandler(settings, store, transaction_manager)


class DatabaseProvider(Provider):
    """SQLite database connection."""

    scope = Scope.APP

    settings = from_context(DatabaseSettings)

    @provide(scope=Scope.REQUEST)
    async def connection(self, settings: DatabaseSettings) -> AsyncIterator[aiosqlite.Connection]:
        """Provide a request-scoped aiosqlite connection.

        Yields:
            An aiosqlite database connection.

        """
        db = await aiosqlite.connect(settings.path)
        db.row_factory = aiosqlite.Row
        yield db
        await db.close()


def create_container() -> AsyncContainer:
    """Create and return the consumer DI container.

    Returns:
        Configured async container.

    """
    settings = get_settings()
    return make_async_container(
        ConfigProvider(),
        AdapterProvider(),
        HandlerProvider(),
        DatabaseProvider(),
        context={
            AppSettings: settings.app,
            RabbitSettings: settings.rabbit,
            DatabaseSettings: settings.database,
            ProcessingSettings: settings.processing,
        },
    )
