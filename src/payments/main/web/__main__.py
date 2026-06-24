"""Web server entry point."""

import uvicorn

from payments.main.config import get_settings
from payments.main.web.entrypoint import create_app  # noqa: F401


def run_web() -> None:
    """Run the web server with uvicorn."""
    settings = get_settings()

    uvicorn.run(
        "payments.main.web.entrypoint:create_app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.reload,
        factory=True,
    )


if __name__ == "__main__":
    run_web()
