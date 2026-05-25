"""P2P trading — read-only tools.

Endpoint paths are best-effort: ByBit V5 P2P docs are sparser than the rest;
the official `pybit` SDK is the most reliable reference. If a particular tool
returns ``retCode 10005`` (Permission denied) or ``retCode 10003`` (API key
permission missing) on your account — that means your key does not have the
P2P scope enabled or your region/KYC blocks P2P; the tool will surface a
graceful error envelope rather than crash.

Mutating P2P operations (create_ad, delete_ad, cancel_order, release_order,
mark_paid, send_message, appeal, confirm_payment) are intentionally excluded.
"""

from __future__ import annotations

from typing import Any

from .._runtime import post
from ..server import mcp


@mcp.tool()
def p2p_get_account_info() -> dict[str, Any]:
    """P2P account info: nickname, completion rate, level, payment methods.

    Per Bybit V5 spec all P2P endpoints are POST (even read-only ones).
    """
    return post("/v5/p2p/user/personal/info", body={})


@mcp.tool()
def p2p_get_ads_list(
    token_id: str | None = None,
    currency_id: str | None = None,
    side: str | None = None,
    payment: list[str] | None = None,
    size: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """Public marketplace ads.

    Args:
        side: ``0`` (BUY ads — they want to buy crypto) / ``1`` (SELL ads).
    """
    body: dict[str, Any] = {"size": str(size), "page": str(page)}
    if token_id:
        body["tokenId"] = token_id
    if currency_id:
        body["currencyId"] = currency_id
    if side:
        body["side"] = [side] if isinstance(side, str) else side
    if payment:
        body["payment"] = payment
    return post("/v5/p2p/item/online", body=body)


@mcp.tool()
def p2p_get_my_ads(
    item_id: str | None = None,
    status: str | None = None,
    side: str | None = None,
    token_id: str | None = None,
    currency_id: str | None = None,
    page: int = 1,
    size: int = 20,
) -> dict[str, Any]:
    """My own P2P ads."""
    body: dict[str, Any] = {"page": str(page), "size": str(size)}
    for k, v in (
        ("itemId", item_id),
        ("status", status),
        ("side", side),
        ("tokenId", token_id),
        ("currencyId", currency_id),
    ):
        if v is not None:
            body[k] = v
    return post("/v5/p2p/item/personal/list", body=body)


@mcp.tool()
def p2p_get_ad_info(item_id: str) -> dict[str, Any]:
    """Single ad details by id."""
    return post("/v5/p2p/item/info", body={"itemId": item_id})


def _p2p_orders_body(
    *,
    status: int | None,
    begin_time: str | None,
    end_time: str | None,
    token_id: str | None,
    side: int | None,
    page: int,
    size: int,
) -> dict[str, Any]:
    """Build the request body for both P2P order-list endpoints.

    Bybit caps ``size`` at 30 — values above that make the API silently return
    ``result: {}`` (no count/items, no error). We raise early instead.
    """
    if not 1 <= size <= 30:
        raise ValueError(f"P2P size must be in [1, 30], got {size}")
    if page < 1:
        raise ValueError(f"P2P page must be >= 1, got {page}")
    body: dict[str, Any] = {"page": page, "size": size}
    for k, v in (
        ("status", status),
        ("beginTime", begin_time),
        ("endTime", end_time),
        ("tokenId", token_id),
        ("side", side),
    ):
        if v is not None:
            body[k] = v
    return body


@mcp.tool()
def p2p_get_orders(
    status: int | None = None,
    begin_time: str | None = None,
    end_time: str | None = None,
    token_id: str | None = None,
    side: int | None = None,
    page: int = 1,
    size: int = 30,
) -> dict[str, Any]:
    """My P2P orders, all statuses (`/v5/p2p/order/simplifyList`).

    By default returns orders from the last 90 days. Max history window 180 days.
    Returns ``{count, items}`` per Bybit P2P spec.

    Args:
        status: Order status. ``5`` waiting for chain confirm /
            ``10`` waiting for buyer payment / ``20`` waiting for seller release /
            ``30`` appealing / ``40`` cancelled / ``50`` finished /
            ``60`` paying-failed / ``70`` time-out-cancelled / ``80`` cancelling.
        begin_time/end_time: **String** timestamps in ms (e.g. ``"1700000000000"``).
        side: Single integer — ``0`` Buy / ``1`` Sell.
        page: Page number, 1-based.
        size: Rows per page, 1-30 (max 30 enforced).
    """
    return post(
        "/v5/p2p/order/simplifyList",
        body=_p2p_orders_body(
            status=status,
            begin_time=begin_time,
            end_time=end_time,
            token_id=token_id,
            side=side,
            page=page,
            size=size,
        ),
    )


@mcp.tool()
def p2p_get_pending_orders(
    status: int | None = None,
    begin_time: str | None = None,
    end_time: str | None = None,
    token_id: str | None = None,
    side: int | None = None,
    page: int = 1,
    size: int = 30,
) -> dict[str, Any]:
    """Pending (active) P2P orders only (`/v5/p2p/order/pending/simplifyList`).

    Same request shape as ``p2p_get_orders`` — see its docstring for status/side
    enums. Size capped at 30 (otherwise Bybit returns empty ``result: {}``).
    """
    return post(
        "/v5/p2p/order/pending/simplifyList",
        body=_p2p_orders_body(
            status=status,
            begin_time=begin_time,
            end_time=end_time,
            token_id=token_id,
            side=side,
            page=page,
            size=size,
        ),
    )


@mcp.tool()
def p2p_get_order_info(order_id: str) -> dict[str, Any]:
    """Single P2P-order details."""
    return post("/v5/p2p/order/info", body={"orderId": order_id})


@mcp.tool()
def p2p_get_chat_messages(
    order_id: str,
    start_message_id: str | None = None,
    size: int = 20,
) -> dict[str, Any]:
    """Chat history for a P2P order."""
    body: dict[str, Any] = {"orderId": order_id, "size": size}
    if start_message_id:
        body["startMessageId"] = start_message_id
    return post("/v5/p2p/order/message/listpage", body=body)


@mcp.tool()
def p2p_get_payment_methods() -> dict[str, Any]:
    """List of the user's configured P2P payment methods."""
    return post("/v5/p2p/user/payment/list", body={})


@mcp.tool()
def p2p_get_counterparty_info(
    original_uid: str | None = None,
    order_id: str | None = None,
) -> dict[str, Any]:
    """Counter-party reputation for a P2P trade (`/v5/p2p/user/order/personal/info`).

    Note the path has ``order`` segment — different from
    ``p2p_get_account_info`` (own account) at ``/v5/p2p/user/personal/info``.

    Args:
        original_uid: Counterparty UID.
        order_id: Specific P2P order id (required by Bybit per pybit reference).
    """
    body: dict[str, Any] = {}
    if original_uid:
        body["originalUid"] = original_uid
    if order_id:
        body["orderId"] = order_id
    return post("/v5/p2p/user/order/personal/info", body=body)
