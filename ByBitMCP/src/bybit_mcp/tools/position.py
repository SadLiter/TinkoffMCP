"""PositionService — open positions, closed P&L, position-move history."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .._runtime import get
from ..serialize import decimal_str, to_decimal
from ..server import mcp


def _enrich_positions(result: dict[str, Any]) -> dict[str, Any]:
    """Add a ``pnl`` block per position: cost_basis, current_value, absolute & %."""
    positions = result.get("list", []) if isinstance(result, dict) else []
    enriched = []
    for pos in positions:
        size = to_decimal(pos.get("size"))
        avg = to_decimal(pos.get("avgPrice"))
        mark = to_decimal(pos.get("markPrice"))
        position_value = to_decimal(pos.get("positionValue"))
        un_pnl_api = to_decimal(pos.get("unrealisedPnl"))
        side = pos.get("side")  # "Buy" / "Sell"

        cost_basis: Decimal | None = None
        current_value: Decimal | None = None
        pnl_abs: Decimal | None = None
        pnl_pct: Decimal | None = None

        if size and avg:
            cost_basis = (size * avg).quantize(Decimal("0.00000001"))
        if position_value is not None:
            current_value = position_value
        elif size and mark:
            current_value = (size * mark).quantize(Decimal("0.00000001"))

        if cost_basis is not None and current_value is not None:
            diff = current_value - cost_basis
            if side == "Sell":
                diff = -diff
            pnl_abs = diff.quantize(Decimal("0.00000001"))
            if cost_basis != 0:
                pnl_pct = (diff / cost_basis * 100).quantize(Decimal("0.01"))
        else:
            pnl_abs = un_pnl_api

        enriched.append(
            {
                "symbol": pos.get("symbol"),
                "side": side,
                "size": pos.get("size"),
                "leverage": pos.get("leverage"),
                "entry_price": pos.get("avgPrice"),
                "mark_price": pos.get("markPrice"),
                "liq_price": pos.get("liqPrice"),
                "cost_basis": decimal_str(cost_basis),
                "current_value": decimal_str(current_value),
                "pnl_absolute": decimal_str(pnl_abs),
                "pnl_percent": decimal_str(pnl_pct),
                "unrealised_pnl_api": pos.get("unrealisedPnl"),
                "cum_realised_pnl": pos.get("cumRealisedPnl"),
                "cur_realised_pnl": pos.get("curRealisedPnl"),
                "position_status": pos.get("positionStatus"),
                "position_idx": pos.get("positionIdx"),
            }
        )
    return {**result, "pnl": enriched}


@mcp.tool()
def position_get_list(
    category: str = "linear",
    symbol: str | None = None,
    base_coin: str | None = None,
    settle_coin: str | None = None,
    limit: int = 200,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Open positions with **pre-computed P&L per position**.

    Each item in ``pnl[]`` carries: symbol, side, size, leverage, entry_price,
    mark_price, liq_price, cost_basis, current_value, pnl_absolute, pnl_percent.

    Args:
        category: ``linear`` (USDT/USDC perps & futures), ``inverse``, ``option``.
            Spot has no position concept — use ``account_get_wallet_balance``.
        symbol: Optional single-symbol filter.
        settle_coin: e.g. ``USDT`` — required for category=linear if no symbol.
    """
    res = get(
        "/v5/position/list",
        params={
            "category": category,
            "symbol": symbol,
            "baseCoin": base_coin,
            "settleCoin": settle_coin,
            "limit": limit,
            "cursor": cursor,
        },
    )
    if isinstance(res, dict) and not res.get("error"):
        return _enrich_positions(res)
    return res


@mcp.tool()
def position_get_closed_pnl(
    category: str = "linear",
    symbol: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Realised-P&L history of closed positions."""
    return get(
        "/v5/position/closed-pnl",
        params={
            "category": category,
            "symbol": symbol,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def position_get_move_history(
    category: str | None = None,
    symbol: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    status: str | None = None,
    block_trade_id: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> dict[str, Any]:
    """History of position-move (block-trade) operations.

    Args:
        status: ``Processing`` / ``Filled`` / ``Rejected``.
    """
    return get(
        "/v5/position/move-history",
        params={
            "category": category,
            "symbol": symbol,
            "startTime": start_time,
            "endTime": end_time,
            "status": status,
            "blockTradeId": block_trade_id,
            "limit": limit,
            "cursor": cursor,
        },
    )
