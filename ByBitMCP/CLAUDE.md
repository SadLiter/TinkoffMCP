# Project Instructions for AI Agents

**Git/GitHub Policy:** see [../CLAUDE.md](../CLAUDE.md) — the monorepo-level policy applies here verbatim. TL;DR: agents must NOT perform any git/GitHub write operations (`git commit`, `git push`, `gh pr create`, GitHub MCP `create_*/update_*/push_*/merge_*/delete_*/issue_write/pull_request_review_write`, etc.). User commits and pushes manually.

## Build & Test

```bash
uv sync --group dev               # install runtime + dev deps (ruff)
uv run ruff format src/           # format
uv run ruff check src/            # lint — must pass before PR
uv run bybit-mcp                  # smoke-start the MCP server (Ctrl+C to stop)
```

Smoke-test stdio cleanliness (required — JSON-RPC channel must not be polluted):

```bash
BYBIT_API_KEY=dummy BYBIT_API_SECRET=dummy uv run bybit-mcp >/tmp/out.log 2>/tmp/err.log < /dev/null &
sleep 1; kill %1 2>/dev/null
wc -c /tmp/out.log   # must be 0
```

After renaming the parent directory (e.g. into `InvestMCPs/`), regenerate the venv:

```bash
rm -rf .venv && uv sync
```

## Architecture

Stdio MCP server (FastMCP) → `httpx.Client` with HMAC-SHA256 signing per ByBit V5 spec.
All numeric values are Decimal-strings (ByBit returns numbers as strings; we keep that
and only round computed fields).

Read-only by design. Mutating endpoints (PostOrder, CancelOrder, transfers, withdrawals,
purchase, redeem, …) are **intentionally not exposed**. Services without a public V5
REST API (peer-to-peer Bybit Pay namespace, ByX publications) are not implemented;
see README "Что НЕ реализовано".

## Conventions

- One MCP tool function per ByBit V5 read endpoint.
- Tool names prefixed by service bucket: `market_*`, `account_*`, `position_*`, `order_*`,
  `asset_*`, `user_*`, `spotmargin_*`, `earn_*`/`loan_*`, `p2p_*`, `card_*`.
- API errors (non-zero `retCode`, HTTP 4xx/5xx) are caught and returned as a JSON envelope
  `{error: true, ret_code, ret_msg, http_status}` — they never raise into the MCP runtime.
- Logs go to stderr only. Never `print()`. Never log the API secret or full signature.
