"""Numeric helpers for ByBit V5 responses.

ByBit returns numeric values as JSON strings (``"123.45"``), which preserves
precision. We therefore do *not* re-format every response — we just pass it
through. The helpers here are used by tool modules that need to compute
derived fields (P&L, cost basis, percentages) without ever falling into float.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def to_decimal(value: Any) -> Decimal | None:
    """Coerce an API value (string, number, None, dict-with-value) into Decimal."""
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        # Some endpoints return MoneyValue-like dicts. Fall back to value field.
        return to_decimal(value.get("value"))
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def decimal_str(value: Decimal | None, *, places: int | None = None) -> str | None:
    """Format a Decimal as a plain (non-scientific) string."""
    if value is None:
        return None
    if places is not None:
        try:
            quant = Decimal(1).scaleb(-places)
            value = value.quantize(quant)
        except (InvalidOperation, ValueError):
            pass
    return format(value, "f")


def safe_div(num: Decimal | None, den: Decimal | None) -> Decimal | None:
    """Return ``num / den`` or ``None`` if either operand is missing or denominator is zero."""
    if num is None or den is None or den == 0:
        return None
    return num / den
