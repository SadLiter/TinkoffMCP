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


@mcp.tool()
def p2p_get_orders(
    status: int | None = None,
    begin_time: int | None = None,
    end_time: int | None = None,
    token_id: str | None = None,
    side: list[int] | None = None,
    page: int = 1,
    size: int = 20,
) -> dict[str, Any]:
    """My P2P orders (all statuses).

    Args:
        status: 5=waiting for chain confirm, 10=waiting for buyer payment,
            20=waiting for seller release, 30=appealing, 40=cancelled,
            50=finished, 60=paying-failed, 70=time-out-cancelled, 80=cancelling.
        side: ``[0]`` buy / ``[1]`` sell.
    """
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
    return post("/v5/p2p/order/simplifyList", body=body)


@mcp.tool()
def p2p_get_pending_orders(
    status: int | None = None,
    begin_time: int | None = None,
    end_time: int | None = None,
    token_id: str | None = None,
    side: list[int] | None = None,
    page: int = 1,
    size: int = 20,
) -> dict[str, Any]:
    """Pending (active) P2P orders only."""
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
    return post("/v5/p2p/order/pending/simplifyList", body=body)


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
    counter_party_user_id: str | None = None,
) -> dict[str, Any]:
    """Counter-party reputation info for a P2P trade."""
    body: dict[str, Any] = {}
    if original_uid:
        body["originalUid"] = original_uid
    if counter_party_user_id:
        body["counterPartyUserId"] = counter_party_user_id
    return post("/v5/p2p/user/personal/info", body=body)
