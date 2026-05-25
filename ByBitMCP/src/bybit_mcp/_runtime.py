"""Shared runtime helpers for tool modules.

Centralises the pattern: pull the shared HTTP client, call the API, and
translate any ByBit / network error into a JSON-serialisable envelope so
the MCP runtime never sees a raised exception.
"""

from __future__ import annotations

import logging
from typing import Any

from .client import ByBitAPIError, ByBitConfigError, ByBitError, _redact
from .server import get_client

logger = logging.getLogger(__name__)


def call(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    private: bool = True,
) -> Any:
    """Invoke ByBit ``METHOD path``, surface errors as ``{error: True, ...}`` dicts."""
    try:
        return get_client().call(method, path, params=params, body=body, private=private)
    except ByBitAPIError as exc:
        logger.warning("%s %s API error: %s", method, path, exc)
        return exc.to_dict()
    except ByBitConfigError as exc:
        # Missing credentials / bad config — not a bug, no traceback.
        logger.warning("%s %s config error: %s", method, path, exc)
        return {
            "error": True,
            "ret_code": "config_error",
            "ret_msg": _redact(str(exc)) or "",
            "http_status": None,
        }
    except ByBitError as exc:
        logger.exception("%s %s client error", method, path)
        return {
            "error": True,
            "ret_code": "client_error",
            "ret_msg": _redact(str(exc)) or "",
            "http_status": None,
        }
    except Exception as exc:  # last-resort guard (see comment below)
        # `Exception`, not `BaseException`, so KeyboardInterrupt / SystemExit
        # / GeneratorExit still propagate and let the stdio loop shut down.
        logger.exception("%s %s unexpected error", method, path)
        return {
            "error": True,
            "ret_code": exc.__class__.__name__,
            "ret_msg": _redact(str(exc)) or "",
            "http_status": None,
        }


def get(path: str, params: dict[str, Any] | None = None, *, private: bool = True) -> Any:
    return call("GET", path, params=params, private=private)


def post(
    path: str,
    body: dict[str, Any] | None = None,
    *,
    params: dict[str, Any] | None = None,
    private: bool = True,
) -> Any:
    return call("POST", path, params=params, body=body, private=private)


__all__ = ["call", "get", "post"]
