"""FastMCP server entry point.

* stdio transport — JSON-RPC flows over stdin/stdout, so nothing else may
  touch stdout (logging, prints, traceback dumps — all stderr).
* The :class:`TInvestClient` is constructed lazily at startup from the
  ``INVEST_TOKEN`` env var.
* Each tool module is responsible for registering its own ``@mcp.tool()``
  functions; they all share the module-level ``mcp`` instance and pull
  the client via :func:`get_client`.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from .client import TInvestClient


def _configure_logging() -> None:
    level_name = os.environ.get("TBANK_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


_configure_logging()
logger = logging.getLogger(__name__)

mcp = FastMCP("tinkoff-mcp")

_client: "TInvestClient | None" = None


def get_client() -> "TInvestClient":
    """Return the shared :class:`TInvestClient`, creating it on first use."""
    global _client
    if _client is None:
        from .client import TInvestClient, TInvestConfigError

        token = os.environ.get("INVEST_TOKEN", "").strip()
        if not token:
            raise TInvestConfigError(
                "INVEST_TOKEN env var is not set. Generate a read-only "
                "T-Invest token at https://www.tbank.ru/invest/settings/api/ "
                "and pass it via the env block in claude_desktop_config.json."
            )
        _client = TInvestClient(token)
        logger.info("TInvestClient initialised")
    return _client


def _register_tools() -> None:
    """Import tool modules so their ``@mcp.tool()`` decorators run."""
    from .tools import (  # noqa: F401
        instruments,
        marketdata,
        operations,
        orders,
        signals,
        stoporders,
        users,
    )


def main() -> None:
    """Console-script entry point — wired in pyproject as ``tinkoff-mcp``."""
    _register_tools()
    logger.info("starting tinkoff-mcp stdio server")
    mcp.run()  # default transport is stdio


if __name__ == "__main__":
    main()
