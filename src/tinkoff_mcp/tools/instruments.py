"""InstrumentsService — instrument catalogue and reference data tools.

Every read-only RPC from the service has a matching tool here. Mutating
methods (``EditFavorites``, ``CreateFavoriteGroup``, ``DeleteFavoriteGroup``)
are intentionally omitted.
"""

from __future__ import annotations

from typing import Any

from .._runtime import call_api
from ..server import mcp

# --- Lists of instruments --------------------------------------------------

_DEFAULT_STATUS = "INSTRUMENT_STATUS_BASE"


def _list_body(
    instrument_status: str | None,
    instrument_exchange: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "instrumentStatus": instrument_status or _DEFAULT_STATUS,
    }
    if instrument_exchange:
        body["instrumentExchange"] = instrument_exchange
    return body


@mcp.tool()
def instruments_shares(
    instrument_status: str = _DEFAULT_STATUS,
    instrument_exchange: str | None = None,
) -> dict[str, Any]:
    """List shares. ``instrument_status``: ``INSTRUMENT_STATUS_BASE`` (default,
    only tradable via API) or ``INSTRUMENT_STATUS_ALL`` (everything)."""
    return call_api("InstrumentsService", "Shares", _list_body(instrument_status, instrument_exchange))


@mcp.tool()
def instruments_bonds(
    instrument_status: str = _DEFAULT_STATUS,
    instrument_exchange: str | None = None,
) -> dict[str, Any]:
    """List bonds. See ``instruments_shares`` for status values."""
    return call_api("InstrumentsService", "Bonds", _list_body(instrument_status, instrument_exchange))


@mcp.tool()
def instruments_etfs(
    instrument_status: str = _DEFAULT_STATUS,
    instrument_exchange: str | None = None,
) -> dict[str, Any]:
    """List ETFs."""
    return call_api("InstrumentsService", "Etfs", _list_body(instrument_status, instrument_exchange))


@mcp.tool()
def instruments_currencies(
    instrument_status: str = _DEFAULT_STATUS,
    instrument_exchange: str | None = None,
) -> dict[str, Any]:
    """List currency pairs traded on the exchange."""
    return call_api("InstrumentsService", "Currencies", _list_body(instrument_status, instrument_exchange))


@mcp.tool()
def instruments_futures(
    instrument_status: str = _DEFAULT_STATUS,
    instrument_exchange: str | None = None,
) -> dict[str, Any]:
    """List futures."""
    return call_api("InstrumentsService", "Futures", _list_body(instrument_status, instrument_exchange))


@mcp.tool()
def instruments_options(
    instrument_status: str = _DEFAULT_STATUS,
    instrument_exchange: str | None = None,
) -> dict[str, Any]:
    """List options (deprecated by the API in favour of ``instruments_options_by``,
    but still returns data)."""
    return call_api("InstrumentsService", "Options", _list_body(instrument_status, instrument_exchange))


@mcp.tool()
def instruments_options_by(
    basic_asset_uid: str | None = None,
    basic_asset_position_uid: str | None = None,
) -> dict[str, Any]:
    """List options filtered by underlying asset.

    Provide either ``basic_asset_uid`` or ``basic_asset_position_uid``.
    """
    body: dict[str, Any] = {}
    if basic_asset_uid:
        body["basicAssetUid"] = basic_asset_uid
    if basic_asset_position_uid:
        body["basicAssetPositionUid"] = basic_asset_position_uid
    return call_api("InstrumentsService", "OptionsBy", body)


@mcp.tool()
def instruments_indicatives(instrument_status: str = _DEFAULT_STATUS) -> dict[str, Any]:
    """List indicative (non-tradable) instruments like indexes."""
    return call_api("InstrumentsService", "Indicatives", {"instrumentStatus": instrument_status})


# --- Single-instrument lookups --------------------------------------------


def _by_body(id_type: str, id_value: str, class_code: str | None) -> dict[str, Any]:
    body: dict[str, Any] = {"idType": id_type, "id": id_value}
    if class_code:
        body["classCode"] = class_code
    return body


@mcp.tool()
def instruments_share_by(
    id_type: str,
    id: str,
    class_code: str | None = None,
) -> dict[str, Any]:
    """Get a single share. ``id_type``: ``INSTRUMENT_ID_TYPE_FIGI`` /
    ``INSTRUMENT_ID_TYPE_TICKER`` / ``INSTRUMENT_ID_TYPE_UID`` /
    ``INSTRUMENT_ID_TYPE_POSITION_UID``. With TICKER you must also pass
    ``class_code`` (e.g. ``TQBR``)."""
    return call_api("InstrumentsService", "ShareBy", _by_body(id_type, id, class_code))


@mcp.tool()
def instruments_bond_by(id_type: str, id: str, class_code: str | None = None) -> dict[str, Any]:
    """Get a single bond. See ``instruments_share_by`` for ``id_type`` values."""
    return call_api("InstrumentsService", "BondBy", _by_body(id_type, id, class_code))


@mcp.tool()
def instruments_etf_by(id_type: str, id: str, class_code: str | None = None) -> dict[str, Any]:
    """Get a single ETF."""
    return call_api("InstrumentsService", "EtfBy", _by_body(id_type, id, class_code))


@mcp.tool()
def instruments_currency_by(id_type: str, id: str, class_code: str | None = None) -> dict[str, Any]:
    """Get a single currency pair."""
    return call_api("InstrumentsService", "CurrencyBy", _by_body(id_type, id, class_code))


@mcp.tool()
def instruments_future_by(id_type: str, id: str, class_code: str | None = None) -> dict[str, Any]:
    """Get a single futures contract."""
    return call_api("InstrumentsService", "FutureBy", _by_body(id_type, id, class_code))


@mcp.tool()
def instruments_option_by(id_type: str, id: str, class_code: str | None = None) -> dict[str, Any]:
    """Get a single option."""
    return call_api("InstrumentsService", "OptionBy", _by_body(id_type, id, class_code))


@mcp.tool()
def instruments_get_instrument_by(id_type: str, id: str, class_code: str | None = None) -> dict[str, Any]:
    """Generic single-instrument lookup (works across all instrument types)."""
    return call_api("InstrumentsService", "GetInstrumentBy", _by_body(id_type, id, class_code))


# --- Search ----------------------------------------------------------------


@mcp.tool()
def instruments_find_instrument(
    query: str,
    instrument_kind: str | None = None,
    api_trade_available_flag: bool | None = None,
) -> dict[str, Any]:
    """Free-text search across all instruments by ticker, ISIN, FIGI or name.

    Args:
        query: Search string.
        instrument_kind: Optional ``InstrumentType`` filter, e.g.
            ``INSTRUMENT_TYPE_SHARE``, ``INSTRUMENT_TYPE_BOND``,
            ``INSTRUMENT_TYPE_ETF``, ``INSTRUMENT_TYPE_FUTURES``,
            ``INSTRUMENT_TYPE_OPTION``, ``INSTRUMENT_TYPE_CURRENCY``.
        api_trade_available_flag: Restrict to instruments tradable via API.
    """
    body: dict[str, Any] = {"query": query}
    if instrument_kind:
        body["instrumentKind"] = instrument_kind
    if api_trade_available_flag is not None:
        body["apiTradeAvailableFlag"] = api_trade_available_flag
    return call_api("InstrumentsService", "FindInstrument", body)


# --- Schedules / reference data -------------------------------------------


@mcp.tool()
def instruments_trading_schedules(
    exchange: str | None = None,
    from_: str | None = None,
    to: str | None = None,
) -> dict[str, Any]:
    """Trading schedules for one or all exchanges in a date range.

    Args:
        exchange: Exchange code (e.g. ``MOEX``, ``SPB``); empty for all.
        from_/to: ISO-8601 timestamps; empty for the current trading day.
    """
    body: dict[str, Any] = {}
    if exchange:
        body["exchange"] = exchange
    if from_:
        body["from"] = from_
    if to:
        body["to"] = to
    return call_api("InstrumentsService", "TradingSchedules", body)


@mcp.tool()
def instruments_get_countries() -> dict[str, Any]:
    """List of country codes the API knows about."""
    return call_api("InstrumentsService", "GetCountries")


@mcp.tool()
def instruments_get_brands(limit: int | None = None, page_token: str | None = None) -> dict[str, Any]:
    """List of brands (parents of instruments)."""
    body: dict[str, Any] = {}
    if limit is not None or page_token is not None:
        body["paging"] = {}
        if limit is not None:
            body["paging"]["limit"] = limit
        if page_token is not None:
            body["paging"]["pageToken"] = page_token
    return call_api("InstrumentsService", "GetBrands", body)


@mcp.tool()
def instruments_get_brand_by(id: str) -> dict[str, Any]:
    """Single brand details by id."""
    return call_api("InstrumentsService", "GetBrandBy", {"id": id})


# --- Dividends / coupons / interests ---------------------------------------


@mcp.tool()
def instruments_get_dividends(
    figi: str | None = None,
    instrument_id: str | None = None,
    from_: str | None = None,
    to: str | None = None,
) -> dict[str, Any]:
    """Dividend payments for a share over a period.

    Args:
        figi: FIGI of the share.
        instrument_id: UID / FIGI / Position UID alternative to ``figi``.
        from_/to: ISO-8601 timestamps.
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
    return call_api("InstrumentsService", "GetDividends", body)


@mcp.tool()
def instruments_get_bond_coupons(
    figi: str | None = None,
    instrument_id: str | None = None,
    from_: str | None = None,
    to: str | None = None,
) -> dict[str, Any]:
    """Coupon payments for a bond."""
    body: dict[str, Any] = {}
    if figi:
        body["figi"] = figi
    if instrument_id:
        body["instrumentId"] = instrument_id
    if from_:
        body["from"] = from_
    if to:
        body["to"] = to
    return call_api("InstrumentsService", "GetBondCoupons", body)


@mcp.tool()
def instruments_get_bond_events(
    instrument_id: str,
    from_: str | None = None,
    to: str | None = None,
    event_type: str | None = None,
) -> dict[str, Any]:
    """Corporate / lifecycle events for a bond (offers, redemptions, etc.).

    Args:
        instrument_id: UID / FIGI of the bond.
        event_type: Optional ``EventType`` enum.
    """
    body: dict[str, Any] = {"instrumentId": instrument_id}
    if from_:
        body["from"] = from_
    if to:
        body["to"] = to
    if event_type:
        body["type"] = event_type
    return call_api("InstrumentsService", "GetBondEvents", body)


@mcp.tool()
def instruments_get_accrued_interests(
    figi: str | None = None,
    instrument_id: str | None = None,
    from_: str | None = None,
    to: str | None = None,
) -> dict[str, Any]:
    """Accrued coupon interest (НКД) history for a bond."""
    body: dict[str, Any] = {}
    if figi:
        body["figi"] = figi
    if instrument_id:
        body["instrumentId"] = instrument_id
    if from_:
        body["from"] = from_
    if to:
        body["to"] = to
    return call_api("InstrumentsService", "GetAccruedInterests", body)


# --- Assets / fundamentals / forecasts -------------------------------------


@mcp.tool()
def instruments_get_assets(
    instrument_type: str | None = None,
    instrument_status: str | None = None,
) -> dict[str, Any]:
    """List of assets (instrument-agnostic). Works for everything except
    futures and options."""
    body: dict[str, Any] = {}
    if instrument_type:
        body["instrumentType"] = instrument_type
    if instrument_status:
        body["instrumentStatus"] = instrument_status
    return call_api("InstrumentsService", "GetAssets", body)


@mcp.tool()
def instruments_get_asset_by(id: str) -> dict[str, Any]:
    """Single asset by id (uid)."""
    return call_api("InstrumentsService", "GetAssetBy", {"id": id})


@mcp.tool()
def instruments_get_asset_fundamentals(assets: list[str]) -> dict[str, Any]:
    """Fundamentals for a list of asset UIDs (revenue, P/E, EPS, etc.)."""
    return call_api("InstrumentsService", "GetAssetFundamentals", {"assets": assets})


@mcp.tool()
def instruments_get_asset_reports(
    instrument_id: str,
    from_: str | None = None,
    to: str | None = None,
) -> dict[str, Any]:
    """Issuer financial reports for an asset.

    Args:
        instrument_id: UID of the asset.
    """
    body: dict[str, Any] = {"instrumentId": instrument_id}
    if from_:
        body["from"] = from_
    if to:
        body["to"] = to
    return call_api("InstrumentsService", "GetAssetReports", body)


@mcp.tool()
def instruments_get_consensus_forecasts(
    page: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    """Consensus analyst forecasts across all covered instruments, paginated."""
    return call_api(
        "InstrumentsService",
        "GetConsensusForecasts",
        {"paging": {"page": page, "limit": limit}},
    )


@mcp.tool()
def instruments_get_forecast_by(instrument_id: str) -> dict[str, Any]:
    """Consensus forecast for one instrument by UID."""
    return call_api(
        "InstrumentsService",
        "GetForecastBy",
        {"instrumentId": instrument_id},
    )


@mcp.tool()
def instruments_get_favorites(group_id: str | None = None) -> dict[str, Any]:
    """User's favourites list (in optional named group)."""
    body: dict[str, Any] = {}
    if group_id:
        body["groupId"] = group_id
    return call_api("InstrumentsService", "GetFavorites", body)


@mcp.tool()
def instruments_get_risk_rates(
    instrument_id: str | None = None,
) -> dict[str, Any]:
    """Risk rates (k_long / k_short / d_long / d_short) for a specific
    instrument or for all if ``instrument_id`` is omitted."""
    body: dict[str, Any] = {}
    if instrument_id:
        body["instrumentId"] = instrument_id
    return call_api("InstrumentsService", "GetRiskRates", body)
