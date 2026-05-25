"""UsersService — read-only account and tariff tools."""

from __future__ import annotations

from typing import Any

from .._runtime import call_api
from ..server import mcp


@mcp.tool()
def users_get_accounts() -> dict[str, Any]:
    """List all brokerage and IIS accounts available for the current token.

    Returns each account's id, name, type (brokerage / IIS), status, access
    level and opening date. Use the returned ``id`` value as ``account_id``
    for every other tool that operates on a specific account.
    """
    return call_api("UsersService", "GetAccounts")


@mcp.tool()
def users_get_info() -> dict[str, Any]:
    """Return user-level info: premium status, qualified-investor status,
    tariff name, and list of asset classes the user is qualified for.

    Useful when deciding which instruments the user can trade or to
    understand applicable rate limits.
    """
    return call_api("UsersService", "GetInfo")


@mcp.tool()
def users_get_margin_attributes(account_id: str) -> dict[str, Any]:
    """Margin requirements and risk metrics for a single account.

    Args:
        account_id: Account identifier (from ``users_get_accounts``).
    """
    return call_api("UsersService", "GetMarginAttributes", {"accountId": account_id})


@mcp.tool()
def users_get_user_tariff() -> dict[str, Any]:
    """Current API tariff and quota: unary-method limits per minute and
    streaming-connection limits per type."""
    return call_api("UsersService", "GetUserTariff")
