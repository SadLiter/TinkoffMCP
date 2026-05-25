"""AccountService — wallet, balance, margin, fees. Includes P&L enrichment."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .._runtime import get
from ..serialize import decimal_str, to_decimal
from ..server import mcp


def _enrich_wallet(result: dict[str, Any]) -> dict[str, Any]:
    """Add a top-level ``pnl`` block with the convenient roll-up."""
    accounts = result.get("list", []) if isinstance(result, dict) else []
    if not accounts:
        return result
    acc = accounts[0]
    coin_blocks = []
    for c in acc.get("coin", []):
        eq = to_decimal(c.get("equity"))
        if not eq or eq == 0:
            continue
        coin_blocks.append(
            {
                "coin": c.get("coin"),
                "wallet_balance": c.get("walletBalance"),
                "equity": c.get("equity"),
                "unrealised_pnl": c.get("unrealisedPnl"),
                "cum_realised_pnl": c.get("cumRealisedPnl"),
                "usd_value": c.get("usdValue"),
                "available_to_withdraw": c.get("availableToWithdraw"),
                "borrow_amount": c.get("borrowAmount"),
                "locked": c.get("locked"),
            }
        )
    pnl = {
        "account_type": acc.get("accountType"),
        "total_equity": acc.get("totalEquity"),
        "total_wallet_balance": acc.get("totalWalletBalance"),
        "total_margin_balance": acc.get("totalMarginBalance"),
        "total_available_balance": acc.get("totalAvailableBalance"),
        "total_perp_unrealised_pnl": acc.get("totalPerpUPL"),
        "total_initial_margin": acc.get("totalInitialMargin"),
        "total_maintenance_margin": acc.get("totalMaintenanceMargin"),
        "by_coin": coin_blocks,
        "note": (
            "USD-equivalent totals come straight from the API. by_coin filters "
            "to non-zero equity. All values are strings — preserve precision."
        ),
    }
    return {**result, "pnl": pnl}


@mcp.tool()
def account_get_wallet_balance(
    account_type: str = "UNIFIED",
    coin: str | None = None,
) -> dict[str, Any]:
    """Wallet balance with enriched P&L summary.

    Args:
        account_type: ``UNIFIED`` (Unified Trading Account, default), ``CONTRACT``
            (Inverse Derivatives), ``SPOT`` (legacy classic spot — rarely used now).
        coin: Comma-separated coin filter, e.g. ``BTC,USDT``. Empty = all.
    """
    res = get(
        "/v5/account/wallet-balance",
        params={"accountType": account_type, "coin": coin},
    )
    if isinstance(res, dict) and not res.get("error"):
        return _enrich_wallet(res)
    return res


@mcp.tool()
def account_get_borrow_history(
    currency: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Margin-borrow history (Unified Account)."""
    return get(
        "/v5/account/borrow-history",
        params={
            "currency": currency,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def account_get_collateral_info(currency: str | None = None) -> dict[str, Any]:
    """Collateral information for Unified Account."""
    return get("/v5/account/collateral-info", params={"currency": currency})


@mcp.tool()
def account_get_coin_greeks(base_coin: str | None = None) -> dict[str, Any]:
    """Option position Greeks (delta, gamma, vega, theta) per base coin."""
    return get("/v5/asset/coin-greeks", params={"baseCoin": base_coin})


@mcp.tool()
def account_get_fee_rate(
    category: str = "linear",
    symbol: str | None = None,
    base_coin: str | None = None,
) -> dict[str, Any]:
    """Taker/maker fee rates for the calling account."""
    return get(
        "/v5/account/fee-rate",
        params={"category": category, "symbol": symbol, "baseCoin": base_coin},
    )


@mcp.tool()
def account_get_account_info() -> dict[str, Any]:
    """Account configuration: unified margin status, margin mode, master-trader flag, etc."""
    return get("/v5/account/info")


@mcp.tool()
def account_get_transaction_log(
    account_type: str | None = None,
    category: str | None = None,
    currency: str | None = None,
    base_coin: str | None = None,
    type: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """UTA transaction log (settlements, transfers, funding, trading fees, etc.).

    Args:
        account_type: ``UNIFIED`` / ``CONTRACT`` / ``SPOT``.
        category: ``linear`` / ``inverse`` / ``option`` / ``spot``.
        type: Transaction type filter — see V5 docs (``TRANSFER_IN``, ``TRADE``,
            ``SETTLEMENT``, ``DELIVERY``, ``LIQUIDATION``, ``BONUS``, ``FEE_REFUND``…).
    """
    return get(
        "/v5/account/transaction-log",
        params={
            "accountType": account_type,
            "category": category,
            "currency": currency,
            "baseCoin": base_coin,
            "type": type,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def account_get_contract_transaction_log(
    currency: str | None = None,
    base_coin: str | None = None,
    type: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Inverse-contract transaction log (classic account)."""
    return get(
        "/v5/account/contract-transaction-log",
        params={
            "currency": currency,
            "baseCoin": base_coin,
            "type": type,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def account_get_smp_group() -> dict[str, Any]:
    """Self-Match-Prevention group id for the calling account."""
    return get("/v5/account/smp-group")


@mcp.tool()
def account_get_mmp_state(base_coin: str) -> dict[str, Any]:
    """Market-Maker Protection state for option market makers.

    Args:
        base_coin: e.g. ``BTC`` / ``ETH``.
    """
    return get("/v5/account/mmp-state", params={"baseCoin": base_coin})


@mcp.tool()
def account_get_pay_info(coin: str | None = None) -> dict[str, Any]:
    """Bybit on-chain Alpha-Trade collateral / borrow info (`/v5/account/pay-info`).

    Despite the name, this V5 endpoint returns lending-style info — current
    collateral list, borrow size, borrow value, available balance — for the
    on-chain trading product (DEX-Alpha). It is the documented endpoint that
    the API-key "Pay" scope controls; Bybit's peer-to-peer Bybit Pay service
    does not expose a public V5 REST namespace.

    Args:
        coin: Filter by coin code (e.g. ``SOL``). Note: only a subset of coins
            is accepted by the endpoint; if you get ``retCode 10001`` (Invalid
            parameter), try omitting the argument to get the full picture.
    """
    return get("/v5/account/pay-info", params={"coin": coin})


@mcp.tool()
def account_get_withdrawal_info(coin_name: str | None = None) -> dict[str, Any]:
    """UTA transferable amount per coin (`/v5/account/withdrawal`).

    Different from `/v5/asset/withdraw/withdrawable-amount` — this is the
    account-level transferable amount in the Unified wallet only.

    Args:
        coin_name: Uppercase coin code. Comma-separated, up to 20 coins
            (e.g. ``"BTC,USDC,USDT,SOL"``). Omit for default coin.
    """
    return get("/v5/account/withdrawal", params={"coinName": coin_name})


@mcp.tool()
def account_get_instruments_info(category: str, symbol: str | None = None) -> dict[str, Any]:
    """UTA-specific instruments info (`/v5/account/instruments-info`).

    Different from public `/v5/market/instruments-info` — this returns the
    instrument set as visible to the calling UTA account.

    Args:
        category: ``linear`` / ``inverse`` / ``option`` / ``spot``.
        symbol: Optional single-symbol filter.
    """
    return get(
        "/v5/account/instruments-info",
        params={"category": category, "symbol": symbol},
    )


@mcp.tool()
def account_get_option_asset_info() -> dict[str, Any]:
    """Option P&L info per coin (`/v5/account/option-asset-info`).

    Returns totalDelta, totalRPL, totalUPL, assetIM, assetMM per coin.
    """
    return get("/v5/account/option-asset-info")


@mcp.tool()
def account_get_dcp_info() -> dict[str, Any]:
    """Disconnect-Cancel-Protect configuration (`/v5/account/query-dcp-info`).

    Requires prior DCP application with a Bybit account manager. Returns dcpStatus
    (`ON`) and timeWindow (3-300 sec) per product (`SPOT`, `DERIVATIVES`, `OPTIONS`).
    """
    return get("/v5/account/query-dcp-info")


@mcp.tool()
def account_get_trade_info_for_analysis(
    category: str | None = None,
    symbol: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Trade-analytics summary endpoint (`/v5/account/trade-info-for-analysis`).

    Returns trade behaviour metrics — win rate, PnL summary, instrument breakdown.
    """
    return get(
        "/v5/account/trade-info-for-analysis",
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
def account_get_user_setting_config() -> dict[str, Any]:
    """User trade-behavior preferences (`/v5/account/user-setting-config`).

    Returns: lpaSpot/lpaPerp (limit-price-adjust flags), deltaEnable (Delta Neutral
    mode), smsef/fmsef (MNT fee-deduction flags).
    """
    return get("/v5/account/user-setting-config")


# Silence unused-import warnings since Decimal/decimal_str may be unused
# until later enrichments.
_ = (Decimal, decimal_str)
