"""OperationsService — money, P&L and history tools.

The headline tool is :func:`operations_get_portfolio`, which augments the
raw API response with a ``pnl`` block holding precomputed per-position
P&L (absolute + percent) plus a roll-up across the whole portfolio. All
numeric values are :class:`decimal.Decimal`-strings to avoid float drift.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from .._runtime import call_api
from ..serialize import decimal_str
from ..server import mcp


def _to_decimal(value: Any) -> Decimal | None:
    """Coerce a serialised number (str, MoneyValue-dict, None) into Decimal."""
    if value is None:
        return None
    if isinstance(value, dict):
        v = value.get("value")
        return _to_decimal(v)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _currency_of(value: Any) -> str | None:
    if isinstance(value, dict):
        c = value.get("currency")
        return c.lower() if isinstance(c, str) else None
    return None


def _enrich_portfolio(portfolio: dict[str, Any]) -> dict[str, Any]:
    """Add a top-level ``pnl`` block plus per-position ``pnl`` entries.

    Per position we compute (all Decimal-strings):
        quantity, average_price, current_price, currency,
        cost_basis, current_value, pnl_absolute, pnl_percent.

    Portfolio-wide we expose:
        total_value, expected_yield_percent,
        breakdown (shares/bonds/etf/currencies/futures/options).
    """
    positions_out = []
    total_cost = Decimal("0")
    total_current = Decimal("0")

    for pos in portfolio.get("positions", []):
        qty = _to_decimal(pos.get("quantity"))
        avg = _to_decimal(pos.get("averagePositionPrice"))
        cur = _to_decimal(pos.get("currentPrice"))
        currency = _currency_of(pos.get("averagePositionPrice")) or _currency_of(
            pos.get("currentPrice")
        )

        cost_basis: Decimal | None = None
        current_value: Decimal | None = None
        pnl_abs: Decimal | None = None
        pnl_pct: Decimal | None = None

        if qty is not None and avg is not None:
            cost_basis = (qty * avg).quantize(Decimal("0.01"))
        if qty is not None and cur is not None:
            current_value = (qty * cur).quantize(Decimal("0.01"))

        # Prefer locally-computed (current_value − cost_basis) for clarity and
        # to avoid the dual-meaning quirk in the API (position-level
        # ``expectedYield`` is in money, portfolio-level is in percent).
        if cost_basis is not None and current_value is not None:
            pnl_abs = (current_value - cost_basis).quantize(Decimal("0.01"))
            if cost_basis != 0:
                pnl_pct = (
                    (current_value - cost_basis) / cost_basis * 100
                ).quantize(Decimal("0.01"))
        else:
            # Fallback: API value (assumed absolute money at position level).
            pnl_abs = _to_decimal(pos.get("expectedYield"))

        pos_pnl = {
            "ticker": pos.get("ticker"),
            "figi": pos.get("figi"),
            "instrument_type": pos.get("instrumentType"),
            "quantity": decimal_str(qty),
            "average_price": decimal_str(avg),
            "current_price": decimal_str(cur),
            "currency": currency,
            "cost_basis": decimal_str(cost_basis),
            "current_value": decimal_str(current_value),
            "pnl_absolute": decimal_str(pnl_abs),
            "pnl_percent": decimal_str(pnl_pct),
        }
        positions_out.append(pos_pnl)

        # Roll-up only for positions priced in the portfolio's base currency.
        # Mixed-currency totals would require FX conversion; we punt and let
        # API's totalAmountPortfolio be the authoritative number.
        if cost_basis is not None:
            total_cost += cost_basis
        if current_value is not None:
            total_current += current_value

    total_value = _to_decimal(portfolio.get("totalAmountPortfolio"))
    expected_yield_pct = _to_decimal(portfolio.get("expectedYield"))

    pnl_block = {
        "total_value": decimal_str(total_value),
        "total_value_currency": _currency_of(portfolio.get("totalAmountPortfolio")),
        "expected_yield_percent": decimal_str(expected_yield_pct),
        "breakdown": {
            "shares": portfolio.get("totalAmountShares"),
            "bonds": portfolio.get("totalAmountBonds"),
            "etf": portfolio.get("totalAmountEtf"),
            "currencies": portfolio.get("totalAmountCurrencies"),
            "futures": portfolio.get("totalAmountFutures"),
            "options": portfolio.get("totalAmountOptions"),
            "sp": portfolio.get("totalAmountSp"),
            "portfolio": portfolio.get("totalAmountPortfolio"),
        },
        "positions": positions_out,
        "note": (
            "pnl_absolute/pnl_percent are computed per-position from "
            "averagePositionPrice and currentPrice. Cross-currency positions "
            "may not roll up cleanly — trust totalAmountPortfolio from the API."
        ),
    }
    return {**portfolio, "pnl": pnl_block}


@mcp.tool()
def operations_get_portfolio(account_id: str) -> dict[str, Any]:
    """Portfolio for an account with **pre-computed P&L per position**.

    The raw API response is preserved under the same keys; on top we add a
    ``pnl`` block that the LLM can rely on without recomputing anything:

    * ``pnl.total_value`` — overall portfolio value (currency in
      ``total_value_currency``)
    * ``pnl.expected_yield_percent`` — overall yield in % (Decimal-string,
      already provided by the API)
    * ``pnl.breakdown`` — per-asset-type subtotals (shares / bonds / etf /
      currencies / futures / options)
    * ``pnl.positions[].pnl_absolute`` / ``pnl_percent`` — per-position P&L
    * ``pnl.positions[].cost_basis`` / ``current_value`` — derived from
      ``averagePositionPrice * quantity`` and ``currentPrice * quantity``.

    Use this tool to answer "how much do I have and am I in the green?".

    Args:
        account_id: Account identifier from ``users_get_accounts``.
    """
    raw = call_api("OperationsService", "GetPortfolio", {"accountId": account_id})
    if isinstance(raw, dict) and not raw.get("error"):
        return _enrich_portfolio(raw)
    return raw


@mcp.tool()
def operations_get_positions(account_id: str) -> dict[str, Any]:
    """Raw positions for an account: money balances per currency,
    securities, futures, options and blocked funds.

    Args:
        account_id: Account identifier from ``users_get_accounts``.
    """
    return call_api("OperationsService", "GetPositions", {"accountId": account_id})


@mcp.tool()
def operations_get_withdraw_limits(account_id: str) -> dict[str, Any]:
    """How much money is free to withdraw, per currency.

    Use this to answer "how much cash do I have?" — these are the funds
    not blocked by open orders, settlement T+ or other locks.

    Args:
        account_id: Account identifier from ``users_get_accounts``.
    """
    return call_api(
        "OperationsService", "GetWithdrawLimits", {"accountId": account_id}
    )


@mcp.tool()
def operations_get_operations(
    account_id: str,
    from_: str,
    to: str,
    state: str = "OPERATION_STATE_UNSPECIFIED",
    figi: str | None = None,
) -> dict[str, Any]:
    """List operations for an account in a time window.

    Args:
        account_id: Account id from ``users_get_accounts``.
        from_: ISO-8601 timestamp (e.g. ``2026-01-01T00:00:00Z``).
        to: ISO-8601 timestamp (e.g. ``2026-05-25T23:59:59Z``).
        state: One of ``OPERATION_STATE_UNSPECIFIED``, ``OPERATION_STATE_EXECUTED``,
            ``OPERATION_STATE_CANCELED``, ``OPERATION_STATE_PROGRESS``.
        figi: Optional FIGI filter — only operations on this instrument.
    """
    body: dict[str, Any] = {
        "accountId": account_id,
        "from": from_,
        "to": to,
        "state": state,
    }
    if figi:
        body["figi"] = figi
    return call_api("OperationsService", "GetOperations", body)


@mcp.tool()
def operations_get_operations_by_cursor(
    account_id: str,
    from_: str | None = None,
    to: str | None = None,
    cursor: str | None = None,
    limit: int = 100,
    instrument_id: str | None = None,
    state: str | None = None,
    operation_types: list[str] | None = None,
    without_commissions: bool = False,
    without_trades: bool = False,
    without_overnights: bool = False,
) -> dict[str, Any]:
    """Paginated operations history — use this for long periods.

    Args:
        account_id: Account id.
        from_/to: ISO-8601 timestamps; leave empty for "as far back as the API allows".
        cursor: Pass ``next_cursor`` from the previous page; empty for first page.
        limit: Page size (1–1000; T-Invest may cap further).
        instrument_id: Optional FIGI / UID / Position UID filter.
        state: ``OPERATION_STATE_EXECUTED`` etc.
        operation_types: List of OperationType enums to keep (e.g. ``['OPERATION_TYPE_BUY','OPERATION_TYPE_SELL']``).
        without_commissions/without_trades/without_overnights: Server-side filters.
    """
    body: dict[str, Any] = {"accountId": account_id, "limit": limit}
    if from_:
        body["from"] = from_
    if to:
        body["to"] = to
    if cursor:
        body["cursor"] = cursor
    if instrument_id:
        body["instrumentId"] = instrument_id
    if state:
        body["state"] = state
    if operation_types:
        body["operationTypes"] = operation_types
    if without_commissions:
        body["withoutCommissions"] = True
    if without_trades:
        body["withoutTrades"] = True
    if without_overnights:
        body["withoutOvernights"] = True
    return call_api("OperationsService", "GetOperationsByCursor", body)


@mcp.tool()
def operations_get_dividends_foreign_issuer(
    account_id: str,
    from_: str | None = None,
    to: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:
    """Foreign-issuer dividends report (two-stage).

    Stage 1 — generate: pass ``account_id``, ``from_`` and ``to``. The
    response contains a ``task_id``.
    Stage 2 — fetch: re-call with the ``task_id`` until the report is ready.
    """
    body: dict[str, Any] = {}
    if task_id:
        body["getDivForeignIssuerReport"] = {"taskId": task_id}
    else:
        body["generateDivForeignIssuerReport"] = {
            "accountId": account_id,
            "from": from_,
            "to": to,
        }
    return call_api("OperationsService", "GetDividendsForeignIssuer", body)


@mcp.tool()
def operations_get_broker_report(
    account_id: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    task_id: str | None = None,
    page: int = 0,
) -> dict[str, Any]:
    """Broker report (two-stage, same pattern as dividends).

    Stage 1: pass ``account_id``, ``from_``, ``to`` to request generation.
    Stage 2: pass ``task_id`` (and optionally ``page``) to fetch.
    """
    body: dict[str, Any] = {}
    if task_id:
        body["getBrokerReportRequest"] = {"taskId": task_id, "page": page}
    else:
        body["generateBrokerReportRequest"] = {
            "accountId": account_id,
            "from": from_,
            "to": to,
        }
    return call_api("OperationsService", "GetBrokerReport", body)
