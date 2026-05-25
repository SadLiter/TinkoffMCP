"""OrdersService — READ-ONLY tools.

Mutating methods (PostOrder, PostOrderAsync, CancelOrder, ReplaceOrder)
are intentionally NOT exposed. The server is read-only by design.
"""

from __future__ import annotations

from typing import Any

from .._runtime import call_api
from ..server import mcp


@mcp.tool()
def orders_get_orders(
    account_id: str,
    from_: str | None = None,
    to: str | None = None,
    execution_status: list[str] | None = None,
) -> dict[str, Any]:
    """List open (and recently closed, if filtered) orders for an account.

    Args:
        account_id: Account id.
        from_/to: ISO-8601 timestamps for the advanced filter window.
        execution_status: Optional list of ``OrderExecutionReportStatus``
            enums to keep (e.g. ``['EXECUTION_REPORT_STATUS_NEW']``).
    """
    body: dict[str, Any] = {"accountId": account_id}
    advanced: dict[str, Any] = {}
    if from_:
        advanced["from"] = from_
    if to:
        advanced["to"] = to
    if execution_status:
        advanced["executionStatus"] = execution_status
    if advanced:
        body["advancedFilters"] = advanced
    return call_api("OrdersService", "GetOrders", body)


@mcp.tool()
def orders_get_order_state(
    account_id: str,
    order_id: str,
    price_type: str | None = None,
    order_id_type: str | None = None,
) -> dict[str, Any]:
    """State (fills, status, commission) of one specific order.

    Args:
        account_id: Account id.
        order_id: Order id from ``orders_get_orders``.
        price_type: Optional ``PRICE_TYPE_POINT`` / ``PRICE_TYPE_CURRENCY``.
        order_id_type: ``ORDER_ID_TYPE_EXCHANGE`` etc.
    """
    body: dict[str, Any] = {"accountId": account_id, "orderId": order_id}
    if price_type:
        body["priceType"] = price_type
    if order_id_type:
        body["orderIdType"] = order_id_type
    return call_api("OrdersService", "GetOrderState", body)


@mcp.tool()
def orders_get_max_lots(
    account_id: str,
    instrument_id: str,
    price: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Maximum number of lots available to buy or short at a given price.

    Args:
        account_id: Account id.
        instrument_id: UID of the instrument.
        price: Optional Quotation ``{"units":"123","nano":0}`` — leaves
            empty for market.
    """
    body: dict[str, Any] = {"accountId": account_id, "instrumentId": instrument_id}
    if price is not None:
        body["price"] = price
    return call_api("OrdersService", "GetMaxLots", body)


@mcp.tool()
def orders_get_order_price(
    account_id: str,
    instrument_id: str,
    price: dict[str, Any],
    direction: str,
    quantity: int,
) -> dict[str, Any]:
    """Compute order price including fees before placing it (read-only —
    nothing is submitted).

    Args:
        account_id: Account id.
        instrument_id: UID of the instrument.
        price: Quotation ``{"units":"123","nano":500000000}``.
        direction: ``ORDER_DIRECTION_BUY`` / ``ORDER_DIRECTION_SELL``.
        quantity: Number of lots.
    """
    return call_api(
        "OrdersService",
        "GetOrderPrice",
        {
            "accountId": account_id,
            "instrumentId": instrument_id,
            "price": price,
            "direction": direction,
            "quantity": quantity,
        },
    )
