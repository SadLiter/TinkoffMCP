"""HTTP client wrapper around the ByBit V5 REST API.

* HMAC-SHA256 signing per spec: ``timestamp + api_key + recv_window + payload``.
* Bearer-style ``X-BAPI-API-KEY`` + signature headers on every private call.
* Public ``/v5/market/*`` endpoints skip signing.
* ByBit returns ``retCode != 0`` at HTTP 200 for application errors — those
  are surfaced as :class:`ByBitAPIError` envelopes, never as exceptions.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import time
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

DEFAULT_API_BASE = "https://api.bybit.com"
TESTNET_API_BASE = "https://api-testnet.bybit.com"
DEFAULT_RECV_WINDOW = 5000
DEFAULT_TIMEOUT = 30.0

# All API paths must match this — guards against future tool authors who
# might wire user input into a path. ByBit V5 paths are strictly /v5/...
_PATH_RE = re.compile(r"^/v5/[A-Za-z0-9/_-]+$")

# Redact API key headers, signatures, and bearer tokens from anything we might log.
# Each rule is (compiled-regex, replacement-string-with-optional-backreferences).
_REDACT_RULES = [
    (
        re.compile(r"X-BAPI-API-KEY:\s*\S+", flags=re.IGNORECASE),
        "X-BAPI-API-KEY: ***",
    ),
    (
        re.compile(r"X-BAPI-SIGN:\s*[0-9a-f]+", flags=re.IGNORECASE),
        "X-BAPI-SIGN: ***",
    ),
    (
        re.compile(r"(Authorization:\s*Bearer\s+)\S+", flags=re.IGNORECASE),
        r"\1***",
    ),
]


class ByBitError(Exception):
    """Base error for all client-side and API-side problems."""


class ByBitConfigError(ByBitError):
    """Bad or missing configuration (token, recv_window, base url, etc.)."""


class ByBitAPIError(ByBitError):
    """Non-zero ``retCode`` or non-2xx response from the ByBit API."""

    def __init__(
        self,
        http_status: int,
        ret_code: int | str | None,
        ret_msg: str,
    ) -> None:
        super().__init__(f"ByBit {ret_code}: {ret_msg}")
        self.http_status = http_status
        self.ret_code = ret_code
        self.ret_msg = _redact(ret_msg) or ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": True,
            "http_status": self.http_status,
            "ret_code": self.ret_code,
            "ret_msg": self.ret_msg,
        }


def _redact(text: str | None) -> str | None:
    if not text:
        return text
    for pat, repl in _REDACT_RULES:
        text = pat.sub(repl, text)
    return text


def _sign(secret: str, timestamp: int, api_key: str, recv_window: int, payload: str) -> str:
    """Compute the X-BAPI-SIGN value per ByBit V5 spec.

    The signed string is concatenation, in order: ``str(timestamp) + api_key +
    str(recv_window) + payload``. ``payload`` is the sorted-urlencoded query
    string for GET, or the raw JSON body for POST.

    Security note: ``secret`` and the concatenated ``raw`` string are local-only
    and MUST NOT be logged or returned. The function only emits the hex digest.
    Anyone refactoring this signature must preserve that invariant — leaking the
    raw string (timestamp + key + recv_window + payload) combined with the
    digest enables HMAC-secret recovery via offline brute force.
    """
    raw = f"{timestamp}{api_key}{recv_window}{payload}"
    return hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()


def _validate_base_url(base: str) -> str:
    base = base.rstrip("/")
    if not base.startswith("https://"):
        raise ByBitConfigError(f"BYBIT_API_BASE must be an https:// URL, got {base!r}")
    return base


class ByBitClient:
    """Synchronous JSON client for the ByBit V5 REST API."""

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        *,
        base_url: str | None = None,
        recv_window: int | None = None,
        timeout: float | None = None,
        testnet: bool | None = None,
    ) -> None:
        # Resolve base URL: explicit > env > testnet flag > mainnet default.
        if base_url is None:
            base_url = os.environ.get("BYBIT_API_BASE", "").strip() or None
        if base_url is None:
            use_testnet = (
                testnet
                if testnet is not None
                else os.environ.get("BYBIT_TESTNET", "").strip() in {"1", "true", "True"}
            )
            base_url = TESTNET_API_BASE if use_testnet else DEFAULT_API_BASE
        base_url = _validate_base_url(base_url)
        if base_url not in {DEFAULT_API_BASE, TESTNET_API_BASE}:
            logger.warning(
                "Using non-default BYBIT_API_BASE=%s — verify you trust this endpoint",
                base_url,
            )

        # Recv window.
        try:
            self._recv_window = int(
                recv_window
                if recv_window is not None
                else os.environ.get("BYBIT_RECV_WINDOW", DEFAULT_RECV_WINDOW)
            )
        except ValueError as exc:
            raise ByBitConfigError(
                f"BYBIT_RECV_WINDOW must be an integer, got {os.environ.get('BYBIT_RECV_WINDOW')!r}"
            ) from exc
        if not 1 <= self._recv_window <= 60000:
            raise ByBitConfigError(
                f"BYBIT_RECV_WINDOW must be in [1, 60000] ms, got {self._recv_window}"
            )

        # Timeout.
        try:
            timeout_value = (
                timeout
                if timeout is not None
                else float(os.environ.get("BYBIT_TIMEOUT", DEFAULT_TIMEOUT))
            )
        except ValueError as exc:
            raise ByBitConfigError(
                f"BYBIT_TIMEOUT must be a number, got {os.environ.get('BYBIT_TIMEOUT')!r}"
            ) from exc
        if not 1 <= timeout_value <= 600:
            raise ByBitConfigError(
                f"BYBIT_TIMEOUT must be in [1, 600] seconds, got {timeout_value}"
            )

        self._api_key = api_key
        self._api_secret = api_secret
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout_value,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "bybit-mcp/0.1",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ByBitClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # ---------------- core call ----------------

    def call(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        private: bool = True,
    ) -> dict[str, Any]:
        """Send a signed (or unsigned) request and return the ``result`` payload.

        Args:
            method: ``GET`` or ``POST``.
            path: Path beginning with ``/v5/...``.
            params: Query parameters (used for GET).
            body: JSON body (used for POST).
            private: If True, sign the request. ``/v5/market/*`` should pass ``False``.
        """
        if not path.startswith("/"):
            path = "/" + path
        if not _PATH_RE.match(path):
            raise ByBitError(f"Invalid V5 API path: {path!r}")
        method = method.upper()
        params = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
        body = body or {}

        headers: dict[str, str] = {}
        if private:
            if not (self._api_key and self._api_secret):
                raise ByBitConfigError(
                    "BYBIT_API_KEY / BYBIT_API_SECRET are not set; cannot call private "
                    f"endpoint {path}. Generate a read-only key at "
                    "https://www.bybit.com/app/user/api-management."
                )
            timestamp = int(time.time() * 1000)
            if method == "GET":
                payload = urlencode(sorted(params.items()))
            else:
                # POST: sign the JSON body (or empty string when there is none).
                # Bybit signs POST requests using only the body — query params on a
                # POST do NOT participate in the signature payload, even when the
                # endpoint accepts params in the URL (e.g. /v5/card/transaction/*).
                payload = json.dumps(body, separators=(",", ":")) if body else ""
            signature = _sign(
                self._api_secret, timestamp, self._api_key, self._recv_window, payload
            )
            headers.update(
                {
                    "X-BAPI-API-KEY": self._api_key,
                    "X-BAPI-TIMESTAMP": str(timestamp),
                    "X-BAPI-RECV-WINDOW": str(self._recv_window),
                    "X-BAPI-SIGN": signature,
                    "X-BAPI-SIGN-TYPE": "2",
                }
            )

        logger.debug(
            "→ %s %s params=%s body_keys=%s private=%s",
            method,
            path,
            sorted(params.keys()),
            sorted(body.keys()) if body else [],
            private,
        )

        try:
            if method == "GET":
                response = self._client.get(path, params=params, headers=headers)
            elif method == "POST":
                response = self._client.post(
                    path,
                    params=params if params else None,
                    json=body if body else None,
                    headers=headers,
                )
            else:
                raise ByBitError(f"Unsupported HTTP method: {method}")
        except httpx.HTTPError as exc:
            raise ByBitError(
                f"Network error calling {method} {path}: "
                f"{exc.__class__.__name__}: {_redact(str(exc))}"
            ) from exc

        # HTTP-level error.
        if response.status_code >= 400:
            text = response.text[:500] if response.text else ""
            raise ByBitAPIError(
                http_status=response.status_code,
                ret_code=None,
                ret_msg=f"HTTP {response.status_code}: {text}",
            )

        # Parse JSON.
        try:
            envelope = response.json()
        except ValueError as exc:
            raise ByBitError(
                f"{method} {path} returned non-JSON body (HTTP {response.status_code})"
            ) from exc

        # ByBit application-level error (HTTP 200 + retCode != 0).
        ret_code = envelope.get("retCode")
        if ret_code is not None and ret_code != 0:
            raise ByBitAPIError(
                http_status=response.status_code,
                ret_code=ret_code,
                ret_msg=envelope.get("retMsg", ""),
            )

        if logger.isEnabledFor(logging.DEBUG):
            result = envelope.get("result")
            shape = sorted(result.keys()) if isinstance(result, dict) else type(result).__name__
            logger.debug("← %s %s result=%s", method, path, shape)

        return envelope.get("result") or {}

    # ---------------- convenience ----------------

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        private: bool = True,
    ) -> dict[str, Any]:
        return self.call("GET", path, params=params, private=private)

    def post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        private: bool = True,
    ) -> dict[str, Any]:
        return self.call("POST", path, body=body, private=private)
