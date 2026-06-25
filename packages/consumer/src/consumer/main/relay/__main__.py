"""Consumer relay runner."""

import asyncio

from consumer.main.relay.entrypoint import run_relay

if __name__ == "__main__":
    asyncio.run(run_relay())
