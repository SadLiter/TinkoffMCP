"""HTTP client wrapper around the T-Invest REST API.

Single shared :class:`httpx.Client`, Bearer auth, JSON in and out, TLS CA
bundle, and a uniform :class:`TInvestAPIError` for API-level failures.
"""

from __future__ import annotations

import logging
import os
import re
from importlib import resources
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_SERVICE_METHOD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
_BEARER_RE = re.compile(r"Bearer\s+\S+", flags=re.IGNORECASE)

DEFAULT_API_BASE = "https://invest-public-api.tbank.ru/rest"
DEFAULT_TIMEOUT = 30.0
SERVICE_PREFIX = "tinkoff.public.invest.api.contract.v1"


class TInvestError(Exception):
    """Base error for all client-side and API-side problems."""


class TInvestConfigError(TInvestError):
    """Bad or missing configuration (token, CA bundle, etc.)."""


class TInvestAPIError(TInvestError):
    """Non-2xx response from the T-Invest API.

    ``code`` and ``description`` are taken from the API error envelope:
    https://developer.tbank.ru/invest/intro/developer/errors
    """

    def __init__(
        self,
        http_status: int,
        code: str | int | None,
        message: str,
        description: str | None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.code = code
        self.message = _redact(message)
        self.description = _redact(description)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": True,
            "http_status": self.http_status,
            "code": self.code,
            "message": self.message,
            "description": self.description,
        }


def _redact(text: str | None) -> str | None:
    """Strip any ``Bearer <token>`` substring from log/error text."""
    if not text:
        return text
    return _BEARER_RE.sub("Bearer ***", text)


def _resolve_ca_bundle() -> str | bool:
    """Pick a CA bundle for TLS verification.

    Resolution order:
    1. ``TBANK_CA_BUNDLE`` env var, if set and points to an existing file.
    2. Repository checkout: ``<repo>/certs/russian_trusted_ca.pem`` if the
       package is being run from a source tree.
    3. Installed wheel: ``tinkoff_mcp/_certs/russian_trusted_ca.pem`` via
       :mod:`importlib.resources`.
    4. ``True`` — fall back to the standard ``certifi`` bundle (will fail
       against ``*.tbank.ru`` until Russian Trusted CA is in the OS store).
    """
    env = os.environ.get("TBANK_CA_BUNDLE", "").strip()
    if env:
        if Path(env).is_file():
            return env
        raise TInvestConfigError(f"TBANK_CA_BUNDLE points to a missing file: {env}")

    repo_local = Path(__file__).resolve().parents[2] / "certs" / "russian_trusted_ca.pem"
    if repo_local.is_file():
        return str(repo_local)

    try:
        # Chained joinpath() — single-arg form for Python 3.10/3.11
        # compatibility with MultiplexedPath/Traversable.
        resource = (
            resources.files("tinkoff_mcp").joinpath("_certs").joinpath("russian_trusted_ca.pem")
        )
        if resource.is_file():
            # as_file() materialises into a real filesystem path so that
            # httpx (which expects an OS path string for `verify=`) is
            # happy even when the package was installed in a zipped form.
            with resources.as_file(resource) as path:
                return str(path)
    except Exception:  # pragma: no cover - defensive
        logger.debug("CA bundle lookup via importlib.resources failed", exc_info=True)

    logger.warning(
        "No bundled Russian Trusted CA found. TLS validation against "
        "*.tbank.ru will likely fail. Set TBANK_CA_BUNDLE or install the "
        "system CA bundle."
    )
    return True


class TInvestClient:
    """Synchronous JSON client for the T-Invest REST API."""

    def __init__(
        self,
        token: str,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        app_name: str = "tinkoff-mcp",
    ) -> None:
        if not token:
            raise TInvestConfigError(
                "INVEST_TOKEN is empty. Set it to a read-only T-Invest API "
                "token before starting the server."
            )

        base = (base_url or os.environ.get("TBANK_API_BASE") or DEFAULT_API_BASE).rstrip("/")
        if not base.startswith("https://"):
            raise TInvestConfigError(f"TBANK_API_BASE must be an https:// URL, got {base!r}")
        if base != DEFAULT_API_BASE:
            logger.warning(
                "Using non-default TBANK_API_BASE=%s — verify you trust this endpoint",
                base,
            )
        try:
            timeout_value = (
                timeout
                if timeout is not None
                else float(os.environ.get("TBANK_TIMEOUT", DEFAULT_TIMEOUT))
            )
        except ValueError as exc:
            raise TInvestConfigError(
                f"TBANK_TIMEOUT must be a number, got {os.environ.get('TBANK_TIMEOUT')!r}"
            ) from exc

        self._client = httpx.Client(
            base_url=base,
            verify=_resolve_ca_bundle(),
            timeout=timeout_value,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-app-name": app_name,
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> TInvestClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def call(
        self,
        service: str,
        method: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Invoke ``<service>/<method>`` with a JSON body and return JSON.

        ``service`` is the bare service name (e.g. ``UsersService``);
        ``method`` is the bare method name (e.g. ``GetAccounts``).
        """
        if not (_SERVICE_METHOD_RE.match(service) and _SERVICE_METHOD_RE.match(method)):
            raise TInvestError(f"Invalid service/method identifier: {service!r}/{method!r}")
        path = f"/{SERVICE_PREFIX}.{service}/{method}"
        payload = body or {}
        logger.debug("→ %s/%s body_keys=%s", service, method, sorted(payload.keys()))
        try:
            response = self._client.post(path, json=payload)
        except httpx.HTTPError as exc:
            raise TInvestError(
                f"Network error calling {service}/{method}: {exc.__class__.__name__}: {_redact(str(exc))}"
            ) from exc

        if response.status_code >= 400:
            try:
                envelope = response.json()
            except ValueError:
                envelope = {}
            raise TInvestAPIError(
                http_status=response.status_code,
                code=envelope.get("code"),
                message=envelope.get("message") or response.text[:500],
                description=envelope.get("description"),
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise TInvestError(
                f"{service}/{method} returned non-JSON body (HTTP {response.status_code})"
            ) from exc

        if logger.isEnabledFor(logging.DEBUG):
            shape = sorted(data.keys()) if isinstance(data, dict) else type(data).__name__
            logger.debug("← %s/%s response=%s", service, method, shape)
        return data
