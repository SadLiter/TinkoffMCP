"""MarketService — public market data tools (no API key required)."""

from __future__ import annotations

from typing import Any

from .._runtime import get
from ..server import mcp


@mcp.tool()
def market_get_server_time() -> dict[str, Any]:
    """Get ByBit server time (used for HMAC sync diagnostics)."""
    return get("/v5/market/time", private=False)


@mcp.tool()
def market_get_kline(
    symbol: str,
    interval: str,
    category: str = "linear",
    start: int | None = None,
    end: int | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    """OHLCV candlesticks for an instrument.

    Args:
        symbol: e.g. ``BTCUSDT``.
        interval: 1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, M, W.
        category: ``spot`` / ``linear`` / ``inverse`` / ``option``.
        start/end: milliseconds since epoch (UTC).
        limit: 1-1000 (default 200).
    """
    return get(
        "/v5/market/kline",
        params={
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "start": start,
            "end": end,
            "limit": limit,
        },
        private=False,
    )


@mcp.tool()
def market_get_mark_price_kline(
    symbol: str,
    interval: str,
    category: str = "linear",
    start: int | None = None,
    end: int | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    """Mark-price kline for derivatives."""
    return get(
        "/v5/market/mark-price-kline",
        params={
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "start": start,
            "end": end,
            "limit": limit,
        },
        private=False,
    )


@mcp.tool()
def market_get_index_price_kline(
    symbol: str,
    interval: str,
    category: str = "linear",
    start: int | None = None,
    end: int | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    """Index-price kline."""
    return get(
        "/v5/market/index-price-kline",
        params={
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "start": start,
            "end": end,
            "limit": limit,
        },
        private=False,
    )


@mcp.tool()
def market_get_premium_index_price_kline(
    symbol: str,
    interval: str,
    category: str = "linear",
    start: int | None = None,
    end: int | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    """Premium-index kline (linear perpetual only)."""
    return get(
        "/v5/market/premium-index-price-kline",
        params={
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "start": start,
            "end": end,
            "limit": limit,
        },
        private=False,
    )


@mcp.tool()
def market_get_instruments_info(
    category: str = "linear",
    symbol: str | None = None,
    status: str | None = None,
    base_coin: str | None = None,
    limit: int = 500,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Instrument metadata (tick size, lot size, leverage, etc.)."""
    return get(
        "/v5/market/instruments-info",
        params={
            "category": category,
            "symbol": symbol,
            "status": status,
            "baseCoin": base_coin,
            "limit": limit,
            "cursor": cursor,
        },
        private=False,
    )


@mcp.tool()
def market_get_orderbook(
    symbol: str,
    category: str = "linear",
    limit: int = 25,
) -> dict[str, Any]:
    """Order book snapshot. ``limit`` is depth per side: spot 1-200, linear/inverse 1-500, option 1-25."""
    return get(
        "/v5/market/orderbook",
        params={"category": category, "symbol": symbol, "limit": limit},
        private=False,
    )


@mcp.tool()
def market_get_tickers(
    category: str = "linear",
    symbol: str | None = None,
    base_coin: str | None = None,
    exp_date: str | None = None,
) -> dict[str, Any]:
    """Ticker info for one or all symbols of a category."""
    return get(
        "/v5/market/tickers",
        params={
            "category": category,
            "symbol": symbol,
            "baseCoin": base_coin,
            "expDate": exp_date,
        },
        private=False,
    )


@mcp.tool()
def market_get_funding_rate_history(
    symbol: str,
    category: str = "linear",
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    """Historical funding rate ticks (derivatives)."""
    return get(
        "/v5/market/funding/history",
        params={
            "category": category,
            "symbol": symbol,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        },
        private=False,
    )


@mcp.tool()
def market_get_public_trade_history(
    symbol: str,
    category: str = "linear",
    base_coin: str | None = None,
    option_type: str | None = None,
    limit: int = 60,
) -> dict[str, Any]:
    """Public recent trades."""
    return get(
        "/v5/market/recent-trade",
        params={
            "category": category,
            "symbol": symbol,
            "baseCoin": base_coin,
            "optionType": option_type,
            "limit": limit,
        },
        private=False,
    )


@mcp.tool()
def market_get_open_interest(
    symbol: str,
    interval_time: str = "5min",
    category: str = "linear",
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Open interest history. ``interval_time``: 5min, 15min, 30min, 1h, 4h, 1d."""
    return get(
        "/v5/market/open-interest",
        params={
            "category": category,
            "symbol": symbol,
            "intervalTime": interval_time,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
        private=False,
    )


@mcp.tool()
def market_get_historical_volatility(
    base_coin: str | None = None,
    period: int | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    category: str = "option",
) -> dict[str, Any]:
    """Historical volatility for options."""
    return get(
        "/v5/market/historical-volatility",
        params={
            "category": category,
            "baseCoin": base_coin,
            "period": period,
            "startTime": start_time,
            "endTime": end_time,
        },
        private=False,
    )


@mcp.tool()
def market_get_insurance(coin: str | None = None) -> dict[str, Any]:
    """Insurance pool balance."""
    return get("/v5/market/insurance", params={"coin": coin}, private=False)


@mcp.tool()
def market_get_risk_limit(
    category: str = "linear",
    symbol: str | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Risk-limit configuration per symbol."""
    return get(
        "/v5/market/risk-limit",
        params={"category": category, "symbol": symbol, "cursor": cursor},
        private=False,
    )


@mcp.tool()
def market_get_delivery_price(
    category: str = "option",
    symbol: str | None = None,
    base_coin: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Delivery prices for futures/options."""
    return get(
        "/v5/market/delivery-price",
        params={
            "category": category,
            "symbol": symbol,
            "baseCoin": base_coin,
            "limit": limit,
            "cursor": cursor,
        },
        private=False,
    )


@mcp.tool()
def market_get_long_short_ratio(
    symbol: str,
    period: str = "1h",
    category: str = "linear",
    limit: int = 50,
) -> dict[str, Any]:
    """Long/short ratio history. ``period``: 5min, 15min, 30min, 1h, 4h, 4d."""
    return get(
        "/v5/market/account-ratio",
        params={
            "category": category,
            "symbol": symbol,
            "period": period,
            "limit": limit,
        },
        private=False,
    )
