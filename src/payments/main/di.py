"""Dependency injection container setup."""

from collections.abc import AsyncIterator

from dishka import (
    AsyncContainer,
    Provider,
    Scope,
    from_context,
    make_async_container,
    provide,
    provide_all,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from payments.application.create_payment import CreatePaymentHandler
from payments.application.get_payment import GetPaymentHandler
from payments.application.ports.clock import Clock
from payments.application.ports.event_collector import EventCollector
from payments.application.ports.event_publisher import EventPublisher
from payments.application.ports.payment_gateway import PaymentGateway
from payments.application.ports.transaction_manager import TransactionManager
from payments.application.ports.uuid_generator import UUIDGenerator
from payments.infrastructure.adapters.clock import UTCClock
from payments.infrastructure.adapters.event_collector import InMemoryEventCollector
from payments.infrastructure.adapters.event_publisher import OutboxEventPublisher
from payments.infrastructure.adapters.payment_repository import SqlAlchemyPaymentRepository
from payments.infrastructure.adapters.transaction_manager import SATransactionManager
from payments.infrastructure.adapters.uuid_generator import TimeBasedUUIDGenerator
from payments.main.config import (
    AppSettings,
    OutboxSettings,
    PostgresSettings,
    RabbitSettings,
    get_settings,
)


class ConfigProvider(Provider):
    """Pulls configuration from the container context."""

    scope = Scope.APP

    app_settings = from_context(AppSettings)
    postgres_settings = from_context(PostgresSettings)
    rabbit_settings = from_context(RabbitSettings)
    outbox_settings = from_context(OutboxSettings)


class DatabaseProvider(Provider):
    """SQLAlchemy async engine, sessionmaker, and request-scoped sessions."""

    scope = Scope.APP

    settings = from_context(PostgresSettings)

    @provide
    async def engine(self, settings: PostgresSettings) -> AsyncIterator[AsyncEngine]:
        """Create async engine, dispose on shutdown.

        Yields:
            The async SQLAlchemy engine.

        """
        engine = create_async_engine(settings.uri)
        yield engine
        await engine.dispose()

    @provide
    async def sessionmaker(
        self,
        engine: AsyncEngine,
    ) -> async_sessionmaker[AsyncSession]:
        """Create sessionmaker bound to the engine.

        Returns:
            A sessionmaker factory.

        """
        return async_sessionmaker(
            bind=engine,
            autoflush=False,
            expire_on_commit=False,
        )

    @provide(scope=Scope.REQUEST)
    async def session(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
    ) -> AsyncIterator[AsyncSession]:
        """Provide a request-scoped session.

        Yields:
            An async SQLAlchemy session.

        """
        async with sessionmaker() as session:
            yield session  # noqa: ASYNC119


class AdapterProvider(Provider):
    """Infrastructure adapters bound to their ports."""

    scope = Scope.APP

    clock = provide(UTCClock, provides=Clock)
    uuid_generator = provide(TimeBasedUUIDGenerator, provides=UUIDGenerator)
    payment_gateway = provide(
        SqlAlchemyPaymentRepository,
        provides=PaymentGateway,
        scope=Scope.REQUEST,
    )
    event_collector = provide(
        InMemoryEventCollector,
        provides=EventCollector,
        scope=Scope.REQUEST,
    )
    event_publisher = provide(
        OutboxEventPublisher,
        provides=EventPublisher,
        scope=Scope.REQUEST,
    )
    transaction_manager = provide(
        SATransactionManager,
        provides=TransactionManager,
        scope=Scope.REQUEST,
    )


class HandlerProvider(Provider):
    """Application handlers auto-resolved by dishka."""

    scope = Scope.REQUEST

    handlers = provide_all(
        CreatePaymentHandler,
        GetPaymentHandler,
    )


def create_container(
    *extra_providers: Provider,
    extra_context: dict[type, object] | None = None,
) -> AsyncContainer:
    """Create and return the root DI container.

    Args:
        *extra_providers: Additional dishka providers for specific entrypoints.
        extra_context: Additional context values for the container.

    Returns:
        Configured async container with all providers registered.

    """
    settings = get_settings()
    context: dict[type, object] = {
        AppSettings: settings.app,
        PostgresSettings: settings.postgres,
        RabbitSettings: settings.rabbit,
        OutboxSettings: settings.outbox,
    }
    if extra_context:
        context.update(extra_context)
    return make_async_container(
        ConfigProvider(),
        DatabaseProvider(),
        AdapterProvider(),
        HandlerProvider(),
        *extra_providers,
        context=context,
    )
