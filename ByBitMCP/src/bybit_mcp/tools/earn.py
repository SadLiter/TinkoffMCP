"""Earn + Crypto Loan + Institutional Loan — read-only tools.

Mutating endpoints (purchase, redeem, borrow, repay, lend) are excluded.
"""

from __future__ import annotations

from typing import Any

from .._runtime import get, post
from ..server import mcp

# ---------------- Earn (FlexibleSaving / OnChain) ----------------


@mcp.tool()
def earn_get_product_info(
    category: str,
    coin: str | None = None,
) -> dict[str, Any]:
    """ByBit Earn product catalogue. Public endpoint (no auth needed).

    Args:
        category: REQUIRED. ``FlexibleSaving`` or ``OnChain``.
        coin: Optional coin filter, uppercase (e.g. ``USDT``, ``BTC``).
    """
    return get(
        "/v5/earn/product",
        params={"category": category, "coin": coin},
        private=False,
    )


@mcp.tool()
def earn_get_order_history(
    category: str,
    order_id: str | None = None,
    order_link_id: str | None = None,
    product_id: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Earn stake/redeem order history.

    Args:
        category: REQUIRED. ``FlexibleSaving`` or ``OnChain``.
        order_id / order_link_id: For ``OnChain`` at least one is required.
        start_time / end_time: ms-epoch window; max range 7 days. Default = last 7 days.
        limit: 1-100, default 50.
    """
    return get(
        "/v5/earn/order",
        params={
            "category": category,
            "orderId": order_id,
            "orderLinkId": order_link_id,
            "productId": product_id,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def earn_get_position(
    category: str,
    coin: str | None = None,
    product_id: str | None = None,
) -> dict[str, Any]:
    """Current Earn staked positions.

    Args:
        category: REQUIRED. ``FlexibleSaving`` or ``OnChain``.
        coin: Optional coin filter (uppercase).
        product_id: Optional product id filter.

    For ``OnChain`` only active positions are returned; for ``FlexibleSaving``
    fully-redeemed positions may also appear.
    """
    return get(
        "/v5/earn/position",
        params={
            "category": category,
            "coin": coin,
            "productId": product_id,
        },
    )


# ---------------- Earn Token (byUSDT) ----------------


@mcp.tool()
def earn_get_token_position(coin: str = "BYUSDT") -> dict[str, Any]:
    """Token-Earn position info (currently only ``BYUSDT``).

    Returns totalAmount, totalYield, yesterdayYield, base APR (e8 precision).
    """
    return get("/v5/earn/token/position", params={"coin": coin})


@mcp.tool()
def earn_get_token_orders(
    coin: str = "BYUSDT",
    order_link_id: str | None = None,
    order_id: str | None = None,
    order_type: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Token-Earn order history (currently only ``BYUSDT``).

    Args:
        order_type: ``Stake`` / ``Redeem``.
    """
    return get(
        "/v5/earn/token/order",
        params={
            "coin": coin,
            "orderLinkId": order_link_id,
            "orderId": order_id,
            "orderType": order_type,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


# ---------------- Crypto Loan (retail) ----------------


@mcp.tool()
def loan_get_orders(
    order_id: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Crypto-loan orders (active & historical)."""
    return get(
        "/v5/crypto-loan/borrow-history",
        params={
            "orderId": order_id,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def loan_get_repayment_history(
    order_id: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Crypto-loan repayment history."""
    return get(
        "/v5/crypto-loan/repayment-history",
        params={
            "orderId": order_id,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def loan_get_collateral_info(currency: str | None = None) -> dict[str, Any]:
    """Crypto-loan collateral coin info."""
    return get(
        "/v5/crypto-loan/collateral-data",
        params={"currency": currency},
        private=False,
    )


@mcp.tool()
def loan_get_borrowable_coins() -> dict[str, Any]:
    """Coins available to borrow via Crypto Loan (with rates)."""
    return get("/v5/crypto-loan/loanable-data", private=False)


@mcp.tool()
def loan_get_account_info() -> dict[str, Any]:
    """Crypto-loan account-level info: total debt, collateral value, LTV."""
    return get("/v5/crypto-loan/position")


@mcp.tool()
def loan_get_max_borrowable(
    currency: str,
) -> dict[str, Any]:
    """Max borrowable amount for a given currency, given current collateral."""
    return get(
        "/v5/crypto-loan/max-collateral-amount",
        params={"currency": currency},
    )


# ---------------- Crypto Loan Fixed + Common (newer product) ----------------


@mcp.tool()
def loan_fixed_get_repayment_history(
    repay_id: str | None = None,
    loan_currency: str | None = None,
    limit: str | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Fixed-rate crypto loan repayment history (`/v5/crypto-loan-fixed/repayment-history`).

    Args:
        repay_id: Specific repayment order id.
        loan_currency: Loan coin filter.
        limit: 1-100, default 10. Pass as string.
    """
    return get(
        "/v5/crypto-loan-fixed/repayment-history",
        params={
            "repayId": repay_id,
            "loanCurrency": loan_currency,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def loan_fixed_get_supply_market(
    order_currency: str | None = None,
    term: str | None = None,
    order_by: str | None = None,
    sort: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Fixed-rate lending market quote list (`/v5/crypto-loan-fixed/supply-order-quote`).

    Read-only — available lender offers.

    Args:
        term: Fixed loan duration, e.g. ``7``, ``14``, ``30``, ``90``, ``180`` (days).
        order_by: ``apy`` / ``term`` / ``quantity``.
        sort: ``asc`` / ``desc``.
        limit: 1-100.
    """
    return get(
        "/v5/crypto-loan-fixed/supply-order-quote",
        params={
            "orderCurrency": order_currency,
            "term": term,
            "orderBy": order_by,
            "sort": sort,
            "limit": limit,
        },
    )


@mcp.tool()
def loan_common_get_adjustment_history(
    adjust_id: str | None = None,
    collateral_currency: str | None = None,
    limit: str | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """LTV / collateral adjustment history across crypto-loan products
    (`/v5/crypto-loan-common/adjustment-history`).

    Args:
        adjust_id: Specific adjustment txn id.
        limit: 1-100, default 10. Pass as string.
    """
    return get(
        "/v5/crypto-loan-common/adjustment-history",
        params={
            "adjustId": adjust_id,
            "collateralCurrency": collateral_currency,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def loan_common_get_max_loan(
    currency: str,
    collateral_list: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Max loan amount for a coin given collateral (`/v5/crypto-loan-common/max-loan`).

    POST endpoint but read-only (no side effect).

    Args:
        currency: Coin to borrow.
        collateral_list: Optional list of ``{"ccy": "BTC", "amount": "0.1"}`` —
            balances are checked against the Funding wallet.
    """
    body: dict[str, Any] = {"currency": currency}
    if collateral_list is not None:
        body["collateralList"] = collateral_list
    return post("/v5/crypto-loan-common/max-loan", body=body)
