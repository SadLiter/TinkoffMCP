"""UserService — API key info, account membership, affiliate (read-only)."""

from __future__ import annotations

from typing import Any

from .._runtime import get
from ..server import mcp


@mcp.tool()
def user_get_api_key_information() -> dict[str, Any]:
    """Info about the API key being used: permissions, IP restrictions, expiry."""
    return get("/v5/user/query-api")


@mcp.tool()
def user_get_uid_wallet_type(member_ids: str | None = None) -> dict[str, Any]:
    """Which wallet type (UNIFIED / CLASSIC) each UID is on.

    Args:
        member_ids: Comma-separated UIDs. Empty = current UID.
    """
    return get("/v5/user/get-member-type", params={"memberIds": member_ids})


@mcp.tool()
def user_get_affiliate_user_info(uid: str) -> dict[str, Any]:
    """Affiliate info for a referred user. Needs MASTER trader / affiliate permission."""
    return get("/v5/user/aff-customer-info", params={"uid": uid})


@mcp.tool()
def user_query_sub_members() -> dict[str, Any]:
    """List sub-account UIDs and their statuses (`/v5/user/query-sub-members`).

    Legacy endpoint — for accounts with >10k sub-members use
    ``user_get_sub_members_paginated`` instead.
    """
    return get("/v5/user/query-sub-members")


@mcp.tool()
def user_get_sub_members_paginated(
    page_size: str | None = None,
    next_cursor: str | None = None,
) -> dict[str, Any]:
    """Paginated sub-account list (`/v5/user/submembers`).

    Designed for masters with >10k sub-accounts.

    Args:
        page_size: Records per page (up to 100). String.
        next_cursor: Cursor from previous response's ``nextCursor`` field.
    """
    return get(
        "/v5/user/submembers",
        params={"pageSize": page_size, "nextCursor": next_cursor},
    )


@mcp.tool()
def user_get_escrow_sub_members() -> dict[str, Any]:
    """List escrow sub-members (`/v5/user/escrow_sub_members`)."""
    return get("/v5/user/escrow_sub_members")


@mcp.tool()
def user_get_sub_apikeys(
    sub_member_id: str,
    limit: int = 20,
    cursor: str | None = None,
) -> dict[str, Any]:
    """List all API keys of a sub-UID (`/v5/user/sub-apikeys`).

    Master account only.

    Args:
        sub_member_id: Required. Sub UID.
        limit: 1-20, default 20.
    """
    return get(
        "/v5/user/sub-apikeys",
        params={"subMemberId": sub_member_id, "limit": limit, "cursor": cursor},
    )


@mcp.tool()
def user_get_invitation_referrals(
    status: str | None = None,
    size: str | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Friend referral list (`/v5/user/invitation/referrals`).

    Args:
        status: ``0`` alive / ``1`` invalid. Default: all.
        size: Records per page (1-100). Default 20.
    """
    return get(
        "/v5/user/invitation/referrals",
        params={"status": status, "size": size, "cursor": cursor},
    )
