"""API listener runner."""

import asyncio

from payments.main.listener.entrypoint import run_listener

if __name__ == "__main__":
    asyncio.run(run_listener())
