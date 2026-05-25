"""SignalService — strategies and signals (read-only)."""

from __future__ import annotations

from typing import Any

from .._runtime import call_api
from ..server import mcp


@mcp.tool()
def signals_get_strategies(
    strategy_id: str | None = None,
) -> dict[str, Any]:
    """List signal-providing strategies, optionally filtered to one ``strategy_id``."""
    body: dict[str, Any] = {}
    if strategy_id:
        body["strategyId"] = strategy_id
    return call_api("SignalService", "GetStrategies", body)


@mcp.tool()
def signals_get_signals(
    signal_id: str | None = None,
    strategy_id: str | None = None,
    instrument_uid: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    direction: str | None = None,
    active: str | None = None,
    page: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    """List trading signals with optional filters.

    Args:
        signal_id: Specific signal id.
        strategy_id: Restrict to a strategy.
        instrument_uid: Restrict to an instrument.
        from_/to: ISO-8601 window.
        direction: ``SIGNAL_DIRECTION_BUY`` / ``SIGNAL_DIRECTION_SELL``.
        active: ``SIGNAL_STATE_ACTIVE`` / ``SIGNAL_STATE_CLOSED`` / etc.
        page/limit: Pagination.
    """
    body: dict[str, Any] = {"paging": {"page": page, "limit": limit}}
    if signal_id:
        body["signalId"] = signal_id
    if strategy_id:
        body["strategyId"] = strategy_id
    if instrument_uid:
        body["instrumentUid"] = instrument_uid
    if from_:
        body["from"] = from_
    if to:
        body["to"] = to
    if direction:
        body["direction"] = direction
    if active:
        body["active"] = active
    return call_api("SignalService", "GetSignals", body)
