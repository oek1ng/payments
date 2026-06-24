"""Application configuration via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application-level settings."""

    name: str = "payments"
    env: str = "local"
    debug: bool = True
    title: str = "Payments API"
    log_level: str = "INFO"
    root_path: str = ""
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    api_key: str = "change-me"


class PostgresSettings(BaseSettings):
    """PostgreSQL connection settings."""

    driver: str = "postgresql"
    user: str = "postgres"
    host: str = "localhost"
    password: str = "postgres"  # noqa: S105
    port: int = 5432
    db: str = "payments"

    @property
    def uri(self) -> str:
        """Full async connection URI."""
        return f"{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


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


class OutboxSettings(BaseSettings):
    """Outbox publisher settings."""

    publisher_enabled: bool = True
    batch_size: int = 100
    poll_interval_seconds: float = 1.0
    max_attempts: int = 10
    retry_base_seconds: int = 2


class Settings(BaseSettings):
    """Root application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_max_split=1,
        env_nested_delimiter="_",
        extra="ignore",
    )

    app: AppSettings = AppSettings()
    postgres: PostgresSettings = PostgresSettings()
    rabbit: RabbitSettings = RabbitSettings()
    outbox: OutboxSettings = OutboxSettings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton.

    Returns:
        The application settings.

    """
    return Settings()
