"""MarketDataService — candles, prices, order book and tech analysis."""

from __future__ import annotations

from typing import Any

from .._runtime import call_api
from ..server import mcp


@mcp.tool()
def marketdata_get_candles(
    figi: str | None = None,
    instrument_id: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    interval: str = "CANDLE_INTERVAL_DAY",
    candle_source_type: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """OHLCV candles for an instrument.

    Args:
        figi: FIGI of the instrument (or use ``instrument_id``).
        instrument_id: UID / FIGI / Position UID alternative.
        from_/to: ISO-8601 timestamps.
        interval: One of ``CANDLE_INTERVAL_1_MIN``, ``CANDLE_INTERVAL_2_MIN``,
            ``CANDLE_INTERVAL_3_MIN``, ``CANDLE_INTERVAL_5_MIN``,
            ``CANDLE_INTERVAL_10_MIN``, ``CANDLE_INTERVAL_15_MIN``,
            ``CANDLE_INTERVAL_30_MIN``, ``CANDLE_INTERVAL_HOUR``,
            ``CANDLE_INTERVAL_2_HOUR``, ``CANDLE_INTERVAL_4_HOUR``,
            ``CANDLE_INTERVAL_DAY``, ``CANDLE_INTERVAL_WEEK``,
            ``CANDLE_INTERVAL_MONTH``.
        candle_source_type: Optional ``CANDLE_SOURCE_UNSPECIFIED`` /
            ``CANDLE_SOURCE_EXCHANGE`` / ``CANDLE_SOURCE_INCLUDE_WEEKEND``.
        limit: Optional cap on candle count.
    """
    body: dict[str, Any] = {"interval": interval}
    if figi:
        body["figi"] = figi
    if instrument_id:
        body["instrumentId"] = instrument_id
    if from_:
        body["from"] = from_
    if to:
        body["to"] = to
    if candle_source_type:
        body["candleSourceType"] = candle_source_type
    if limit is not None:
        body["limit"] = limit
    return call_api("MarketDataService", "GetCandles", body)


@mcp.tool()
def marketdata_get_last_prices(
    figi: list[str] | None = None,
    instrument_id: list[str] | None = None,
    last_price_type: str | None = None,
    instrument_status: str | None = None,
) -> dict[str, Any]:
    """Latest known prices for multiple instruments.

    Args:
        figi: List of FIGIs.
        instrument_id: List of UIDs (alternative to ``figi``).
        last_price_type: ``LAST_PRICE_EXCHANGE`` (default) /
            ``LAST_PRICE_DEALER`` / ``LAST_PRICE_UNSPECIFIED``.
        instrument_status: Optional filter on instrument status.
    """
    body: dict[str, Any] = {}
    if figi:
        body["figi"] = figi
    if instrument_id:
        body["instrumentId"] = instrument_id
    if last_price_type:
        body["lastPriceType"] = last_price_type
    if instrument_status:
        body["instrumentStatus"] = instrument_status
    return call_api("MarketDataService", "GetLastPrices", body)


@mcp.tool()
def marketdata_get_close_prices(
    instrument_ids: list[str] | None = None,
    instrument_status: str | None = None,
) -> dict[str, Any]:
    """Closing prices of the previous trading session.

    Args:
        instrument_ids: List of FIGI / UID strings to query (each becomes an
            ``InstrumentClosePriceRequest`` entry).
    """
    body: dict[str, Any] = {}
    if instrument_ids:
        body["instruments"] = [{"instrumentId": x} for x in instrument_ids]
    if instrument_status:
        body["instrumentStatus"] = instrument_status
    return call_api("MarketDataService", "GetClosePrices", body)


@mcp.tool()
def marketdata_get_order_book(
    figi: str | None = None,
    instrument_id: str | None = None,
    depth: int = 20,
) -> dict[str, Any]:
    """Order book snapshot (bids/asks)."""
    body: dict[str, Any] = {"depth": depth}
    if figi:
        body["figi"] = figi
    if instrument_id:
        body["instrumentId"] = instrument_id
    return call_api("MarketDataService", "GetOrderBook", body)


@mcp.tool()
def marketdata_get_trading_status(
    figi: str | None = None,
    instrument_id: str | None = None,
) -> dict[str, Any]:
    """Trading status for one instrument (NORMAL_TRADING / BREAK / etc.)."""
    body: dict[str, Any] = {}
    if figi:
        body["figi"] = figi
    if instrument_id:
        body["instrumentId"] = instrument_id
    return call_api("MarketDataService", "GetTradingStatus", body)


@mcp.tool()
def marketdata_get_trading_statuses(instrument_ids: list[str]) -> dict[str, Any]:
    """Trading status for many instruments at once.

    Args:
        instrument_ids: List of UIDs / FIGIs.
    """
    return call_api(
        "MarketDataService",
        "GetTradingStatuses",
        {"instrumentId": instrument_ids},
    )


@mcp.tool()
def marketdata_get_last_trades(
    figi: str | None = None,
    instrument_id: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    trade_source: str | None = None,
) -> dict[str, Any]:
    """Anonymous last trades for an instrument.

    Args:
        trade_source: Optional ``TRADE_SOURCE_EXCHANGE`` / ``TRADE_SOURCE_DEALER``.
    """
    body: dict[str, Any] = {}
    if figi:
        body["figi"] = figi
    if instrument_id:
        body["instrumentId"] = instrument_id
    if from_:
        body["from"] = from_
    if to:
        body["to"] = to
    if trade_source:
        body["tradeSource"] = trade_source
    return call_api("MarketDataService", "GetLastTrades", body)


@mcp.tool()
def marketdata_get_tech_analysis(
    indicator_type: str,
    instrument_uid: str,
    from_: str,
    to: str,
    interval: str,
    type_of_price: str = "TYPE_OF_PRICE_CLOSE",
    length: int | None = None,
    deviation_multiplier: dict[str, Any] | None = None,
    smoothing: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Compute a technical indicator over a price series.

    Args:
        indicator_type: ``INDICATOR_TYPE_BB`` (Bollinger) / ``_EMA`` /
            ``_RSI`` / ``_MACD`` / ``_SMA``.
        instrument_uid: UID of the instrument.
        from_/to: ISO-8601 window.
        interval: ``INDICATOR_INTERVAL_*`` (mirrors candle intervals).
        type_of_price: ``TYPE_OF_PRICE_CLOSE`` etc.
        length: Period length for the indicator (e.g. 14 for RSI).
        deviation_multiplier: For BB: ``{"units":"2","nano":0}``.
        smoothing: For MACD: ``{"fastLength":12,"slowLength":26,"signalSmoothing":9}``.
    """
    body: dict[str, Any] = {
        "indicatorType": indicator_type,
        "instrumentUid": instrument_uid,
        "from": from_,
        "to": to,
        "interval": interval,
        "typeOfPrice": type_of_price,
    }
    if length is not None:
        body["length"] = length
    if deviation_multiplier is not None:
        body["deviation"] = {"deviationMultiplier": deviation_multiplier}
    if smoothing is not None:
        body["smoothing"] = smoothing
    return call_api("MarketDataService", "GetTechAnalysis", body)
