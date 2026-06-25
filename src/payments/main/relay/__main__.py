"""Outbox relay runner."""

import asyncio

from payments.main.relay.entrypoint import run_relay

if __name__ == "__main__":
    asyncio.run(run_relay())
