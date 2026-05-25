"""FastMCP server entry point for ByBitMCP.

Stdio transport — JSON-RPC flows over stdin/stdout, so nothing may touch
stdout. Logging configured to stderr at module import. The :class:`ByBitClient`
is constructed lazily on first tool invocation, so the server boots even if
``BYBIT_API_KEY`` is unset (private tools will then return an error envelope).
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from .client import ByBitClient


def _configure_logging() -> None:
    level_name = os.environ.get("BYBIT_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


_configure_logging()
logger = logging.getLogger(__name__)

mcp = FastMCP("bybit-mcp")

_client: ByBitClient | None = None


def get_client() -> ByBitClient:
    """Return the shared :class:`ByBitClient`, creating it on first use."""
    global _client
    if _client is None:
        from .client import ByBitClient

        key = os.environ.get("BYBIT_API_KEY", "").strip()
        secret = os.environ.get("BYBIT_API_SECRET", "").strip()
        # We construct the client even with empty creds — public market tools
        # still work; private tools will get a clean ByBitConfigError envelope.
        _client = ByBitClient(key, secret)
        if key and secret:
            logger.info("ByBitClient initialised (with credentials)")
        else:
            logger.warning(
                "ByBitClient initialised without BYBIT_API_KEY/SECRET — "
                "only public /v5/market/* endpoints will work"
            )
    return _client


def _register_tools() -> None:
    """Import tool modules so their ``@mcp.tool()`` decorators run."""
    from .tools import (  # noqa: F401
        account,
        affiliate,
        asset,
        card,
        earn,
        insloan,
        market,
        order,
        p2p,
        position,
        spotmargin,
        user,
    )


def main() -> None:
    """Console-script entry point — wired in pyproject as ``bybit-mcp``."""
    _register_tools()
    logger.info("starting bybit-mcp stdio server")
    mcp.run()  # default transport is stdio


if __name__ == "__main__":
    main()
