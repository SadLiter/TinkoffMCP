"""OrderService — READ-ONLY tools.

Mutating methods (PlaceOrder / AmendOrder / CancelOrder / CancelAllOrders /
BatchPlaceOrder / BatchAmendOrder / BatchCancelOrder) are intentionally NOT
exposed. The server is read-only by design.
"""

from __future__ import annotations

from typing import Any

from .._runtime import get
from ..server import mcp


@mcp.tool()
def order_get_open_orders(
    category: str = "linear",
    symbol: str | None = None,
    base_coin: str | None = None,
    settle_coin: str | None = None,
    order_id: str | None = None,
    order_link_id: str | None = None,
    open_only: int | None = None,
    order_filter: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """List active (and recently closed if requested) orders for an account.

    Args:
        category: ``spot`` / ``linear`` / ``inverse`` / ``option``.
        open_only: 0=untriggered active, 1=triggered/orderbook active, 2=spot conditional.
        order_filter: ``Order`` / ``StopOrder`` / ``tpslOrder`` / ``OcoOrder``.
    """
    return get(
        "/v5/order/realtime",
        params={
            "category": category,
            "symbol": symbol,
            "baseCoin": base_coin,
            "settleCoin": settle_coin,
            "orderId": order_id,
            "orderLinkId": order_link_id,
            "openOnly": open_only,
            "orderFilter": order_filter,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def order_get_history(
    category: str = "linear",
    symbol: str | None = None,
    base_coin: str | None = None,
    settle_coin: str | None = None,
    order_id: str | None = None,
    order_link_id: str | None = None,
    order_filter: str | None = None,
    order_status: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Historical orders (filled, cancelled, rejected, etc.).

    Args:
        order_status: ``New`` / ``PartiallyFilled`` / ``PartiallyFilledCanceled`` /
            ``Filled`` / ``Cancelled`` / ``Untriggered`` / ``Triggered`` /
            ``Deactivated`` / ``Rejected`` / ``Active``.
    """
    return get(
        "/v5/order/history",
        params={
            "category": category,
            "symbol": symbol,
            "baseCoin": base_coin,
            "settleCoin": settle_coin,
            "orderId": order_id,
            "orderLinkId": order_link_id,
            "orderFilter": order_filter,
            "orderStatus": order_status,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def order_get_executions(
    category: str = "linear",
    symbol: str | None = None,
    order_id: str | None = None,
    order_link_id: str | None = None,
    base_coin: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    exec_type: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """User trade executions (fills).

    Args:
        exec_type: ``Trade`` / ``AdlTrade`` / ``Funding`` / ``BustTrade`` / ``Delivery`` /
            ``Settle`` / ``BlockTrade`` / ``MovePosition``.
    """
    return get(
        "/v5/execution/list",
        params={
            "category": category,
            "symbol": symbol,
            "orderId": order_id,
            "orderLinkId": order_link_id,
            "baseCoin": base_coin,
            "startTime": start_time,
            "endTime": end_time,
            "execType": exec_type,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def order_get_spot_borrow_check(symbol: str, side: str) -> dict[str, Any]:
    """How many lots are borrowable for a spot-margin order before placing it.

    Args:
        symbol: e.g. ``BTCUSDT``.
        side: ``Buy`` / ``Sell``.
    """
    return get(
        "/v5/order/spot-borrow-check",
        params={"category": "spot", "symbol": symbol, "side": side},
    )
