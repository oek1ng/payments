"""HTTP API key middleware."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Middleware that validates the X-API-Key header."""

    def __init__(self, app: FastAPI, *, api_key: str) -> None:
        """Initialize the middleware with the expected API key."""
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Check the X-API-Key header before processing the request.

        Returns:
            The response from the next middleware or a 401 error.

        """
        if request.headers.get("X-API-Key") != self._api_key:
            return JSONResponse(status_code=401, content={"detail": "Invalid API key"})
        return await call_next(request)
