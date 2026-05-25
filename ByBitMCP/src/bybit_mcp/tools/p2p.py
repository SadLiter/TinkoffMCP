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


# Bybit P2P order-history caps single-query time window at ~90 days.
# Anything longer comes back as a silent empty `result: {}` — no error,
# indistinguishable from "no orders found". We validate up front instead.
_P2P_MAX_WINDOW_MS = 90 * 24 * 3600 * 1000


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

    Validates everything Bybit silently rejects: ``size`` (1-30), ``page`` (>=1),
    and ``end_time - begin_time`` (<=90 days). When either ``begin_time`` or
    ``end_time`` is given, both must be present.
    """
    if not 1 <= size <= 30:
        raise ValueError(f"P2P size must be in [1, 30], got {size}")
    if page < 1:
        raise ValueError(f"P2P page must be >= 1, got {page}")
    if (begin_time is None) != (end_time is None):
        raise ValueError("P2P begin_time and end_time must be provided together (or both omitted)")
    if begin_time is not None and end_time is not None:
        try:
            b_ms = int(begin_time)
            e_ms = int(end_time)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"P2P begin_time/end_time must be string ms timestamps, "
                f"got {begin_time!r}/{end_time!r}"
            ) from exc
        if e_ms <= b_ms:
            raise ValueError(f"P2P end_time must be > begin_time (got begin={b_ms}, end={e_ms})")
        span_ms = e_ms - b_ms
        if span_ms > _P2P_MAX_WINDOW_MS:
            days = span_ms / 86_400_000
            raise ValueError(
                f"P2P time window must be <= 90 days (got {days:.1f}). "
                "Bybit silently returns empty result for longer windows — "
                "split into 90-day chunks and call repeatedly."
            )

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


def _surface_empty_p2p_response(result: Any, body: dict[str, Any]) -> Any:
    """Convert a silent empty-`{}` P2P response into a structured error envelope.

    Bybit P2P orders endpoints normally return ``{count, items}`` — even when
    there are no orders, ``{count: 0, items: []}`` is returned. A bare ``{}``
    means Bybit silently rejected the request shape and gave us nothing to
    distinguish it from a real success. We surface that explicitly so the LLM
    / user does not interpret it as "no orders".
    """
    if isinstance(result, dict) and not result:
        return {
            "error": True,
            "ret_code": "empty_response",
            "ret_msg": (
                "Bybit returned an empty result `{}` — usually means a parameter "
                "shape was silently rejected. Check size (<=30), time window "
                "(<=90 days), and string-vs-int types."
            ),
            "http_status": 200,
            "request_body": body,
        }
    return result


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

    **Important defaults & limits:**

    * Without ``begin_time``/``end_time`` Bybit returns only the **most recent**
      orders (typically last ~90 days). To see older orders you must pass an
      explicit window.
    * Each query window must be **<= 90 days** (Bybit silently returns
      empty result for longer ranges — we validate up front).
    * To scan a longer history, split into 90-day chunks and call repeatedly.

    Returns ``{count, items}`` per Bybit P2P spec.

    Args:
        status: Order status. ``5`` waiting for chain confirm /
            ``10`` waiting for buyer payment / ``20`` waiting for seller release /
            ``30`` appealing / ``40`` cancelled / ``50`` finished /
            ``60`` paying-failed / ``70`` time-out-cancelled / ``80`` cancelling.
        begin_time/end_time: **String** ms timestamps (e.g. ``"1700000000000"``).
            Both must be provided together or both omitted.
        side: Single integer — ``0`` Buy / ``1`` Sell.
        page: Page number, 1-based.
        size: Rows per page, 1-30 (max 30 enforced).
    """
    body = _p2p_orders_body(
        status=status,
        begin_time=begin_time,
        end_time=end_time,
        token_id=token_id,
        side=side,
        page=page,
        size=size,
    )
    return _surface_empty_p2p_response(post("/v5/p2p/order/simplifyList", body=body), body)


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

    Same request shape and limits as ``p2p_get_orders`` (see its docstring) —
    ``size`` <= 30, time window <= 90 days, both date params together or
    neither. Pending orders are normally short-lived, so the window rarely
    matters in practice.
    """
    body = _p2p_orders_body(
        status=status,
        begin_time=begin_time,
        end_time=end_time,
        token_id=token_id,
        side=side,
        page=page,
        size=size,
    )
    return _surface_empty_p2p_response(post("/v5/p2p/order/pending/simplifyList", body=body), body)


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
