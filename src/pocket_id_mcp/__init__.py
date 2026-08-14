from __future__ import annotations

import asyncio

from .api import PocketIdClient
from .config import Settings
from .server import run_stdio
from .service import PocketIdService


def main() -> None:
    settings = Settings.from_env()
    service = PocketIdService(PocketIdClient(settings), settings)
    asyncio.run(run_stdio(settings, service))


__all__ = ["main"]
