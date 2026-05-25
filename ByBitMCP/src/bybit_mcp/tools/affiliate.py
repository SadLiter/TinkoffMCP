"""AffiliateService — commission queries for affiliate accounts.

Only useful if the API key has the ``Affiliate`` permission scope. For
regular retail accounts the endpoint returns ``retCode 10005`` (Permission
denied) — surfaced as a graceful error envelope by the runtime.
"""

from __future__ import annotations

from typing import Any

from .._runtime import get
from ..server import mcp


@mcp.tool()
def affiliate_get_sub_list(
    cursor: str | None = None,
    size: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sub_aff_id: int | None = None,
) -> dict[str, Any]:
    """List sub-affiliates with commission breakdown (`/v5/affiliate/affiliate-sub-list`).

    Args:
        cursor: Pagination cursor (``nextPageCursor`` from previous response).
        size: Records per page, 1-100. Default 0 (no records).
        start_date: ``YYYY-MM-DD``. Max 3-month window with ``end_date``.
        end_date: ``YYYY-MM-DD``. Must accompany ``start_date``. Both omitted →
            returns T-1 data.
        sub_aff_id: Filter to a specific sub-affiliate; 0 / omit = all.
    """
    return get(
        "/v5/affiliate/affiliate-sub-list",
        params={
            "cursor": cursor,
            "size": size,
            "startDate": start_date,
            "endDate": end_date,
            "subAffId": sub_aff_id,
        },
    )
