"""Shared runtime helpers for tool modules.

Centralises the boilerplate every tool wants: pull the shared HTTP
client, call the API, normalise quotation/money values, and convert any
:class:`TInvestAPIError` into a JSON-serialisable dict (so a failing
tool reports a structured error instead of bubbling an exception up to
the MCP runtime).
"""

from __future__ import annotations

import logging
from typing import Any

from .client import TInvestAPIError, TInvestError, _redact
from .serialize import normalise
from .server import get_client

logger = logging.getLogger(__name__)


def call_api(service: str, method: str, body: dict[str, Any] | None = None) -> Any:
    """Call ``<service>/<method>``, normalise the response, surface errors as dicts.

    Returns either the normalised JSON response or a ``{"error": True, …}``
    payload describing what went wrong. Tools should ``return`` the result
    directly without re-wrapping.
    """
    try:
        raw = get_client().call(service, method, body)
    except TInvestAPIError as exc:
        logger.warning("%s/%s API error: %s", service, method, exc)
        return exc.to_dict()
    except TInvestError as exc:
        logger.exception("%s/%s client error", service, method)
        return {
            "error": True,
            "code": "client_error",
            "message": _redact(str(exc)) or "",
            "description": None,
        }
    except Exception as exc:  # noqa: BLE001 - last-resort guard.
        # We intentionally use `Exception`, not `BaseException`, so that
        # KeyboardInterrupt / SystemExit / GeneratorExit still propagate
        # and let the stdio loop shut down cleanly.
        logger.exception("%s/%s unexpected error", service, method)
        return {
            "error": True,
            "code": exc.__class__.__name__,
            "message": _redact(str(exc)) or "",
            "description": None,
        }
    return normalise(raw)


__all__ = ["call_api"]
