"""Consumer configuration via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application-level settings."""

    name: str = "consumer"
    env: str = "local"
    debug: bool = True
    log_level: str = "INFO"


class RabbitSettings(BaseSettings):
    """RabbitMQ connection settings."""

    host: str = "localhost"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"  # noqa: S105
    vhost: str = "/"

    @property
    def url(self) -> str:
        """Full AMQP connection URL."""
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/{self.vhost}"


class DatabaseSettings(BaseSettings):
    """SQLite database settings."""

    path: str = "consumer.db"


class ProcessingSettings(BaseSettings):
    """Payment processing emulation settings."""

    min_delay_seconds: float = 2.0
    max_delay_seconds: float = 5.0
    success_probability: float = 0.9


class OutboxSettings(BaseSettings):
    """Outbox relay settings."""

    relay_enabled: bool = True
    batch_size: int = 100
    poll_interval_seconds: float = 1.0
    retry_base_seconds: int = 2


class Settings(BaseSettings):
    """Root consumer settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_max_split=1,
        env_nested_delimiter="_",
        extra="ignore",
    )

    app: AppSettings = AppSettings()
    rabbit: RabbitSettings = RabbitSettings()
    database: DatabaseSettings = DatabaseSettings()
    processing: ProcessingSettings = ProcessingSettings()
    outbox: OutboxSettings = OutboxSettings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached consumer settings singleton.

    Returns:
        The consumer settings.

    """
    return Settings()
