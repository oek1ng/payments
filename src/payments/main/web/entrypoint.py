"""Application entrypoint."""

import logging

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from payments.main.bootstrap import (
    setup_http_middlewares,
    setup_http_routes,
    setup_json,
    setup_map_tables,
)
from payments.main.config import get_settings
from payments.main.di import create_container
from payments.presentation.api.http.v1.error_handlers import setup_http_error_handlers

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        The configured FastAPI application instance.

    """
    settings = get_settings()
    app = FastAPI(
        title=settings.app.title,
        debug=settings.app.debug,
        version="0.1.0",
    )
    container = create_container()
    setup_map_tables()
    setup_json()
    setup_http_routes(app)
    setup_dishka(container, app)
    setup_http_middlewares(app, settings=settings)
    setup_http_error_handlers(app)
    logger.info("App created", extra={"app_version": app.version})
    return app
