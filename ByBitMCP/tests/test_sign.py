"""HMAC reference-vector test for client._sign.

This is the only test in the repo right now — its job is to catch any
accidental refactor that breaks signature generation, since a bad signature
means every authenticated tool returns retCode 10004 for the user.
"""

from __future__ import annotations

import hashlib
import hmac

from bybit_mcp.client import _sign


def test_sign_matches_bybit_reference_vector() -> None:
    # Reference from https://bybit-exchange.github.io/docs/v5/guide:
    #   timestamp = 1658385579423, api_key = XXXXXXXXXX, recv_window = 5000,
    #   payload   = '{"category": "option"}'
    # Resulting string to sign: 1658385579423XXXXXXXXXX5000{"category": "option"}
    expected = hmac.new(
        b"s",
        b'1658385579423XXXXXXXXXX5000{"category": "option"}',
        hashlib.sha256,
    ).hexdigest()
    got = _sign("s", 1658385579423, "XXXXXXXXXX", 5000, '{"category": "option"}')
    assert got == expected
    assert len(got) == 64
    assert got == got.lower()


def test_sign_get_style_payload() -> None:
    # GET requests sign urlencode(sorted(params)) as payload.
    expected = hmac.new(
        b"secret",
        b"1700000000000KEY5000accountType=UNIFIED",
        hashlib.sha256,
    ).hexdigest()
    got = _sign("secret", 1700000000000, "KEY", 5000, "accountType=UNIFIED")
    assert got == expected


def test_sign_empty_payload() -> None:
    # POST with empty body → payload is "".
    expected = hmac.new(b"s", b"1700000000000KEY5000", hashlib.sha256).hexdigest()
    got = _sign("s", 1700000000000, "KEY", 5000, "")
    assert got == expected
