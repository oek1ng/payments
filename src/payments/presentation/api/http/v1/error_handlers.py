"""HTTP error handler utilities for FastAPI."""

from functools import partial

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from payments.application.common.exceptions import (
    ApplicationError,
    IdempotencyKeyConflictError,
)


def _error_handler(
    request: Request,  # noqa: ARG001
    exc: ApplicationError,
    status_code: int,
) -> JSONResponse:
    return JSONResponse({"detail": exc.message}, status_code=status_code)


def _internal_error_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


def setup_http_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application."""
    app.add_exception_handler(
        IdempotencyKeyConflictError,
        partial(_error_handler, status_code=409),
    )
    app.add_exception_handler(Exception, _internal_error_handler)
