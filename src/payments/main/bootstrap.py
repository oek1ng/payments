"""Application bootstrap utilities."""

import orjson
from fastapi import APIRouter, FastAPI
from psycopg.types.json import set_json_dumps, set_json_loads

from payments.infrastructure.persistence.tables.payments import map_payments_table
from payments.main.config import Settings
from payments.presentation.api.http.v1 import router
from payments.presentation.api.http.v1.middleware import ApiKeyMiddleware


def setup_json() -> None:
    """Set orjson as the global JSONB serializer and deserializer for psycopg."""
    set_json_dumps(orjson.dumps)
    set_json_loads(orjson.loads)


def setup_map_tables() -> None:
    """Register ORM mappings for all tables."""
    map_payments_table()


def setup_http_routes(app: FastAPI) -> None:
    """Register HTTP routes on the FastAPI application."""
    http_router_v1 = APIRouter(prefix="/v1")
    http_router_v1.include_router(router.router)
    app.include_router(http_router_v1)


def setup_http_middlewares(app: FastAPI, *, settings: Settings) -> None:
    """Register HTTP middlewares on the FastAPI application."""
    app.add_middleware(ApiKeyMiddleware, api_key=settings.app.api_key)  # type: ignore[arg-type]
