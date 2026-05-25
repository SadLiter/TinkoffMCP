"""JSON-side helpers for T-Invest REST responses.

The REST API returns numbers in two shapes:

* Quotation — ``{"units": "10", "nano": 500000000}`` (10.5)
* MoneyValue — ``{"currency": "rub", "units": "10", "nano": 500000000}``

Float would lose precision, so we convert to :class:`decimal.Decimal` and
serialise as a JSON string. We also recursively walk responses to convert
*every* Quotation/MoneyValue we can identify, regardless of nesting depth.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

NANO_SCALE = Decimal(10) ** 9


def quotation_to_decimal(q: dict[str, Any] | None) -> Decimal | None:
    """Convert a Quotation ``{units, nano}`` to :class:`Decimal`."""
    if q is None:
        return None
    units = q.get("units", "0")
    nano = q.get("nano", 0)
    try:
        units_d = Decimal(str(units))
        nano_d = Decimal(int(nano)) / NANO_SCALE
    except (TypeError, ValueError, ArithmeticError):
        return None
    return units_d + nano_d


def money_to_decimal(m: dict[str, Any] | None) -> Decimal | None:
    """Convert a MoneyValue ``{currency, units, nano}`` to :class:`Decimal`.

    Currency is dropped — pair it back manually if you need it.
    """
    return quotation_to_decimal(m)


def _looks_like_quotation(value: dict[str, Any]) -> bool:
    keys = value.keys()
    if not ({"units", "nano"} <= set(keys)):
        return False
    extras = set(keys) - {"units", "nano", "currency"}
    return not extras


def _flatten_quotation(value: dict[str, Any]) -> dict[str, Any] | str | None:
    """Return a JSON-friendly representation of a Quotation/MoneyValue."""
    d = quotation_to_decimal(value)
    if d is None:
        return value
    currency = value.get("currency")
    if currency:
        return {"value": format(d, "f"), "currency": currency}
    return format(d, "f")


def normalise(value: Any) -> Any:
    """Recursively walk a JSON-decoded structure, flattening Quotation/MoneyValue."""
    if isinstance(value, dict):
        if _looks_like_quotation(value):
            return _flatten_quotation(value)
        return {k: normalise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalise(v) for v in value]
    return value


def decimal_str(d: Decimal | None) -> str | None:
    """Format a Decimal as plain string (no scientific notation)."""
    if d is None:
        return None
    return format(d, "f")
