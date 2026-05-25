"""StopOrdersService — READ-ONLY tools.

PostStopOrder and CancelStopOrder are intentionally NOT exposed.
"""

from __future__ import annotations

from typing import Any

from .._runtime import call_api
from ..server import mcp


@mcp.tool()
def stoporders_get_stop_orders(
    account_id: str,
    status: str = "STOP_ORDER_STATUS_OPTION_UNSPECIFIED",
    from_: str | None = None,
    to: str | None = None,
) -> dict[str, Any]:
    """List stop orders on an account.

    Args:
        account_id: Account id.
        status: ``STOP_ORDER_STATUS_OPTION_ACTIVE`` /
            ``STOP_ORDER_STATUS_OPTION_EXECUTED`` /
            ``STOP_ORDER_STATUS_OPTION_CANCELED`` /
            ``STOP_ORDER_STATUS_OPTION_EXPIRED`` /
            ``STOP_ORDER_STATUS_OPTION_UNSPECIFIED`` (default — all).
        from_/to: Optional ISO-8601 window.
    """
    body: dict[str, Any] = {"accountId": account_id, "status": status}
    if from_:
        body["from"] = from_
    if to:
        body["to"] = to
    return call_api("StopOrdersService", "GetStopOrders", body)
