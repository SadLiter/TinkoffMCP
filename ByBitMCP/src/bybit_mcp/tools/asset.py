"""AssetService — deposits, withdrawals, transfers, conversions (read-only)."""

from __future__ import annotations

from typing import Any

from .._runtime import get
from ..server import mcp

# --- Coin / balance lookups ------------------------------------------------


@mcp.tool()
def asset_get_coin_info(coin: str | None = None) -> dict[str, Any]:
    """Per-coin info: status, withdraw min/max, networks, chains, fees."""
    return get("/v5/asset/coin/query-info", params={"coin": coin})


@mcp.tool()
def asset_get_all_coins_balance(
    account_type: str = "FUND",
    coin: str | None = None,
    member_id: str | None = None,
    with_bonus: int | None = None,
) -> dict[str, Any]:
    """Balance per coin for one account type.

    Args:
        account_type: ``UNIFIED`` / ``CONTRACT`` / ``SPOT`` / ``FUND`` / ``INVESTMENT``
            / ``OPTION`` / ``MINING``.
        with_bonus: 1 to include bonus credits.
    """
    return get(
        "/v5/asset/transfer/query-account-coins-balance",
        params={
            "accountType": account_type,
            "coin": coin,
            "memberId": member_id,
            "withBonus": with_bonus,
        },
    )


@mcp.tool()
def asset_get_single_coin_balance(
    account_type: str,
    coin: str,
    member_id: str | None = None,
    to_account_type: str | None = None,
    to_member_id: str | None = None,
    with_bonus: int | None = None,
    with_transfer_safe_amount: int | None = None,
    with_ltv_transfer_safe_amount: int | None = None,
) -> dict[str, Any]:
    """Balance of a single coin in a single account."""
    return get(
        "/v5/asset/transfer/query-account-coin-balance",
        params={
            "accountType": account_type,
            "coin": coin,
            "memberId": member_id,
            "toAccountType": to_account_type,
            "toMemberId": to_member_id,
            "withBonus": with_bonus,
            "withTransferSafeAmount": with_transfer_safe_amount,
            "withLtvTransferSafeAmount": with_ltv_transfer_safe_amount,
        },
    )


@mcp.tool()
def asset_get_transferable_coin(from_account_type: str, to_account_type: str) -> dict[str, Any]:
    """List of coins that can be transferred between two account types."""
    return get(
        "/v5/asset/transfer/query-transfer-coin-list",
        params={
            "fromAccountType": from_account_type,
            "toAccountType": to_account_type,
        },
    )


@mcp.tool()
def asset_get_asset_info(account_type: str = "SPOT", coin: str | None = None) -> dict[str, Any]:
    """Asset summary for the SPOT (classic) account."""
    return get(
        "/v5/asset/transfer/query-asset-info",
        params={"accountType": account_type, "coin": coin},
    )


# --- Transfers (records only — no creation) --------------------------------


@mcp.tool()
def asset_get_internal_transfer_records(
    transfer_id: str | None = None,
    coin: str | None = None,
    status: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Internal transfer history (between your own account types)."""
    return get(
        "/v5/asset/transfer/query-inter-transfer-list",
        params={
            "transferId": transfer_id,
            "coin": coin,
            "status": status,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def asset_get_universal_transfer_records(
    transfer_id: str | None = None,
    coin: str | None = None,
    status: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Universal transfer history (between UIDs / sub-accounts)."""
    return get(
        "/v5/asset/transfer/query-universal-transfer-list",
        params={
            "transferId": transfer_id,
            "coin": coin,
            "status": status,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def asset_get_sub_uid() -> dict[str, Any]:
    """Sub-account UIDs that the parent owns."""
    return get("/v5/asset/transfer/query-sub-member-list")


# --- Deposits (read-only) --------------------------------------------------


@mcp.tool()
def asset_get_allowed_deposit_coin_info(
    coin: str | None = None,
    chain: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Coins permitted for deposit (by chain)."""
    return get(
        "/v5/asset/deposit/query-allowed-list",
        params={"coin": coin, "chain": chain, "limit": limit, "cursor": cursor},
    )


@mcp.tool()
def asset_get_deposit_records(
    coin: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """On-chain deposit history."""
    return get(
        "/v5/asset/deposit/query-record",
        params={
            "coin": coin,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def asset_get_sub_deposit_records(
    sub_member_id: str,
    coin: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Sub-account on-chain deposit history."""
    return get(
        "/v5/asset/deposit/query-sub-member-record",
        params={
            "subMemberId": sub_member_id,
            "coin": coin,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def asset_get_internal_deposit_records(
    coin: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Internal-deposit history (deposits from other ByBit users)."""
    return get(
        "/v5/asset/deposit/query-internal-record",
        params={
            "coin": coin,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def asset_get_master_deposit_address(
    coin: str,
    chain_type: str | None = None,
) -> dict[str, Any]:
    """Master-account deposit address for a coin."""
    return get(
        "/v5/asset/deposit/query-address",
        params={"coin": coin, "chainType": chain_type},
    )


@mcp.tool()
def asset_get_sub_deposit_address(
    coin: str,
    chain_type: str,
    sub_member_id: str,
) -> dict[str, Any]:
    """Sub-account deposit address for a coin."""
    return get(
        "/v5/asset/deposit/query-sub-member-address",
        params={
            "coin": coin,
            "chainType": chain_type,
            "subMemberId": sub_member_id,
        },
    )


# --- Withdrawals (read-only — no submission) ------------------------------


@mcp.tool()
def asset_get_withdrawal_records(
    withdraw_id: str | None = None,
    tx_id: str | None = None,
    coin: str | None = None,
    withdraw_type: int | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Withdrawal history.

    Args:
        withdraw_type: 0=on-chain, 1=internal, 2=all.
    """
    return get(
        "/v5/asset/withdraw/query-record",
        params={
            "withdrawID": withdraw_id,
            "txID": tx_id,
            "coin": coin,
            "withdrawType": withdraw_type,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def asset_get_withdrawable_amount(coin: str) -> dict[str, Any]:
    """How much of a coin can currently be withdrawn (after holds / margin)."""
    return get("/v5/asset/withdraw/withdrawable-amount", params={"coin": coin})


# --- Convert / exchange / delivery / settlement ---------------------------


@mcp.tool()
def asset_get_convert_coin_list(
    account_type: str = "eb_convert_uta",
    side: int = 0,
    coin: str | None = None,
) -> dict[str, Any]:
    """Coins convertible via the Bybit Convert endpoint.

    Args:
        account_type: ``eb_convert_uta`` (Unified) / ``eb_convert_funding`` / ``eb_convert_inverse``.
        side: 0=from-coin list, 1=to-coin list.
    """
    return get(
        "/v5/asset/exchange/query-coin-list",
        params={"accountType": account_type, "side": side, "coin": coin},
    )


@mcp.tool()
def asset_get_convert_status(
    quote_tx_id: str, account_type: str = "eb_convert_uta"
) -> dict[str, Any]:
    """Status of an existing convert quote/transaction (read-only)."""
    return get(
        "/v5/asset/exchange/convert-result-query",
        params={"quoteTxId": quote_tx_id, "accountType": account_type},
    )


@mcp.tool()
def asset_get_convert_history(
    account_type: str | None = None,
    index: int | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """User convert transactions history."""
    return get(
        "/v5/asset/exchange/query-convert-history",
        params={"accountType": account_type, "index": index, "limit": limit},
    )


@mcp.tool()
def asset_get_exchange_records(
    from_coin: str | None = None,
    to_coin: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Coin-to-coin exchange records (legacy endpoint)."""
    return get(
        "/v5/asset/exchange/order-record",
        params={
            "fromCoin": from_coin,
            "toCoin": to_coin,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def asset_get_delivery_record(
    category: str = "linear",
    symbol: str | None = None,
    exp_date: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Futures/options delivery records for the calling account."""
    return get(
        "/v5/asset/delivery-record",
        params={
            "category": category,
            "symbol": symbol,
            "expDate": exp_date,
            "limit": limit,
            "cursor": cursor,
        },
    )


@mcp.tool()
def asset_get_session_settlement(
    category: str = "linear",
    symbol: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """USDC perpetual session-settlement records."""
    return get(
        "/v5/asset/settlement-record",
        params={
            "category": category,
            "symbol": symbol,
            "limit": limit,
            "cursor": cursor,
        },
    )
