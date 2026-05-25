"""Bybit Card — read-only tools.

Bybit Card is the crypto-funded debit card. Availability depends on KYC level
and region. All Card endpoints are **POST with empty body and params in query**
per the V5 spec. If your account is not enrolled in Bybit Card you will get
``retCode 10005`` (Permission denied) or a similar envelope — that is graceful,
not a crash.

Mutating Card endpoints (apply, freeze, change-PIN, top-up) are intentionally
excluded.
"""

from __future__ import annotations

from typing import Any

from .._runtime import post
from ..server import mcp


@mcp.tool()
def card_get_transactions(
    limit: int = 100,
    page: int = 1,
    status_code: str | None = None,
    pan4: str | None = None,
    create_begin_time: int | None = None,
    create_end_time: int | None = None,
    merch_name: str | None = None,
    type: str | None = None,
    txn_id: str | None = None,
    card_token: str | None = None,
    order_no: str | None = None,
) -> dict[str, Any]:
    """Card transaction history (purchases, refunds, authorizations).

    Args:
        limit: 1-500, default 100.
        page: 1+, default 1.
        status_code: ``0`` Pending / ``1`` Cleared / ``2`` Declined.
        pan4: Last 2 or 4 digits of card number (filter to a specific card).
        create_begin_time/create_end_time: ms epoch.
        merch_name: Fuzzy merchant-name search.
        type: ``SIDE_QUERY_AUTH`` (authorization) / ``SIDE_QUERY_FINANCIAL``
            (clearing) / ``SIDE_QUERY_REFUND``.
    """
    # Card query endpoints take parameters in the URL query string even on POST
    # (Bybit docs show "POST /v5/card/transaction/query-asset-records?limit=10&page=1").
    params: dict[str, Any] = {"limit": limit, "page": page}
    for k, v in (
        ("statusCode", status_code),
        ("pan4", pan4),
        ("createBeginTime", create_begin_time),
        ("createEndTime", create_end_time),
        ("merchName", merch_name),
        ("type", type),
        ("txnId", txn_id),
        ("cardToken", card_token),
        ("orderNo", order_no),
    ):
        if v is not None:
            params[k] = v
    return post("/v5/card/transaction/query-asset-records", params=params)


@mcp.tool()
def card_get_points_balance() -> dict[str, Any]:
    """Card reward-point balance (available, pending, settlement period)."""
    return post("/v5/card/reward/points/balance", body={})


@mcp.tool()
def card_get_points_records(
    type: str | None = None,
    side: str | None = None,
    page_size: int = 10,
    page_no: int = 1,
    start_time: int | None = None,
    end_time: int | None = None,
    out_order_id: str | None = None,
    biz_id: str | None = None,
    biz_txn_id: str | None = None,
) -> dict[str, Any]:
    """Card reward-point earn/spend history.

    Args:
        side: ``1`` Earn points / ``2`` Deduct points.
    """
    # Card points-records likewise takes params in the URL query string.
    params: dict[str, Any] = {"pageSize": page_size, "pageNo": page_no}
    for k, v in (
        ("type", type),
        ("side", side),
        ("startTime", start_time),
        ("endTime", end_time),
        ("outOrderId", out_order_id),
        ("bizId", biz_id),
        ("bizTxnId", biz_txn_id),
    ):
        if v is not None:
            params[k] = v
    return post("/v5/card/reward/points/records", params=params)


@mcp.tool()
def card_get_points_tier() -> dict[str, Any]:
    """Card reward tier (GOLD / etc.), used and total spending limit, auto-cashback flag."""
    return post("/v5/card/reward/points/tier", body={})
