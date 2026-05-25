"""Institutional-Loan (OTC) — read-only tools.

These endpoints require the API key to be issued under an institutional
sub-account (Bybit's OTC desk). Retail accounts will get ``retCode 10005``
(Permission denied) — surfaced as a graceful envelope.

Mutating institutional endpoints (borrow / repay / liquidate / convert) are
intentionally NOT exposed.
"""

from __future__ import annotations

from typing import Any

from .._runtime import get
from ..server import mcp


@mcp.tool()
def insloan_get_product_infos(product_id: str | None = None) -> dict[str, Any]:
    """List available institutional-loan products (`/v5/ins-loan/product-infos`).

    Args:
        product_id: Optional filter to a single product.
    """
    return get("/v5/ins-loan/product-infos", params={"productId": product_id})


@mcp.tool()
def insloan_get_loan_orders(
    order_id: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Institutional-loan order list (`/v5/ins-loan/loan-order`).

    Args:
        start_time / end_time: ms-epoch window.
        limit: 1-100, default 100.
    """
    return get(
        "/v5/ins-loan/loan-order",
        params={
            "orderId": order_id,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        },
    )


@mcp.tool()
def insloan_get_repaid_history(
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Institutional-loan repayment history (`/v5/ins-loan/repaid-history`).

    Default window: last 2 years.

    Args:
        limit: 1-100, default 100.
    """
    return get(
        "/v5/ins-loan/repaid-history",
        params={
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        },
    )


@mcp.tool()
def insloan_get_ltv_convert() -> dict[str, Any]:
    """LTV / collateral conversion info (`/v5/ins-loan/ltv-convert`)."""
    return get("/v5/ins-loan/ltv-convert")


@mcp.tool()
def insloan_get_ensure_tokens_convert() -> dict[str, Any]:
    """Margin-tokens convert info (`/v5/ins-loan/ensure-tokens-convert`)."""
    return get("/v5/ins-loan/ensure-tokens-convert")
