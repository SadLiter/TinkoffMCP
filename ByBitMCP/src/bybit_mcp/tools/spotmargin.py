"""Spot-Margin (Unified Trading Account) — read-only tools.

Mutating endpoints (set leverage, borrow, repay, switch mode) are excluded.
"""

from __future__ import annotations

from typing import Any

from .._runtime import get
from ..server import mcp


@mcp.tool()
def spotmargin_get_state() -> dict[str, Any]:
    """Current spot-margin status and configured leverage."""
    return get("/v5/spot-margin-trade/state")


@mcp.tool()
def spotmargin_get_vip_margin_data() -> dict[str, Any]:
    """Public VIP margin tiers and rates."""
    return get("/v5/spot-margin-trade/data", private=False)


@mcp.tool()
def spotmargin_get_borrow_records(
    currency: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Spot-margin borrow history."""
    return get(
        "/v5/spot-margin-trade/borrow-history",
        params={
            "currency": currency,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def spotmargin_get_interest_records(
    currency: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Spot-margin interest charge history."""
    return get(
        "/v5/spot-margin-trade/interest-rate-history",
        params={
            "currency": currency,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )
