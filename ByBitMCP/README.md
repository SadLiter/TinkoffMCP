# ByBitMCP — read-only ByBit для Claude

Неофициальный MCP-сервер для **ByBit V5 API** — 88 read-only тулзов через 11 сервисов. Подключается к Claude Desktop (или любому MCP-клиенту) и даёт LLM-агенту читать ваш ByBit-аккаунт: баланс кошелька, открытые/закрытые позиции, P&L (реализованный и нереализованный), историю сделок, депозиты/выводы, P2P-ордера, Earn-позиции, карту Bybit и рыночные данные.

> ⚠️ **Дисклеймер.** Проект **неофициальный**, никак не связан с ByBit Fintech Ltd. и не одобрен биржей. Сервер работает **только на чтение**: все мутирующие методы (PostOrder, CancelOrder, transfers, withdrawals, purchase/redeem и т.п.) **намеренно не реализованы и не импортируются**. Выпускайте read-only API-ключ — в худшем случае утечки кто-то увидит ваш баланс и историю.

Под капотом — прямые REST-вызовы к `https://api.bybit.com` через `httpx`, HMAC-SHA256-подпись запросов. Стек минимален: `mcp[cli]` и `httpx`.

---

## Что умеет

Tools сгруппированы по сервисам V5 API.

### Market (публичные, без ключа)
`market_get_server_time`, `market_get_kline`, `market_get_mark_price_kline`, `market_get_index_price_kline`, `market_get_premium_index_price_kline`, `market_get_instruments_info`, `market_get_orderbook`, `market_get_tickers`, `market_get_funding_rate_history`, `market_get_public_trade_history`, `market_get_open_interest`, `market_get_historical_volatility`, `market_get_insurance`, `market_get_risk_limit`, `market_get_delivery_price`, `market_get_long_short_ratio`.

### Account — баланс и P&L
- `account_get_wallet_balance` — **главный метод по деньгам**. Возвращает по каждой монете equity, walletBalance, unrealisedPnl, availableToWithdraw, плюс totals по аккаунту в USD. **Дополнительно отдаётся блок `pnl`** с готовой сводкой: total_equity, total_unrealised_pnl, by_coin.
- `account_get_pay_info` — Bybit Pay info по монете (`/v5/account/pay-info`).
- `account_get_borrow_history`, `account_get_collateral_info`, `account_get_coin_greeks`, `account_get_fee_rate`, `account_get_account_info`, `account_get_transaction_log`, `account_get_contract_transaction_log`, `account_get_smp_group`, `account_get_mmp_state`.

### Position — позиции и реализованный P&L
- `position_get_list` — открытые позиции с unrealisedPnl, leverage, liqPrice. **Дополнительно `pnl` блок per-position**: cost_basis, current_value, pnl_absolute, pnl_percent.
- `position_get_closed_pnl` — история закрытых позиций с реализованным P&L.
- `position_get_move_history`.

### Order — заявки и сделки (только чтение)
- `order_get_open_orders` — активные ордера.
- `order_get_history` — история ордеров.
- `order_get_executions` — история исполнений.
- `order_get_spot_borrow_check`.

### Asset — депозиты, выводы, переводы (read-only)
`asset_get_coin_info`, `asset_get_all_coins_balance`, `asset_get_single_coin_balance`, `asset_get_transferable_coin`, `asset_get_internal_transfer_records`, `asset_get_universal_transfer_records`, `asset_get_deposit_records`, `asset_get_sub_deposit_records`, `asset_get_internal_deposit_records`, `asset_get_master_deposit_address`, `asset_get_sub_deposit_address`, `asset_get_allowed_deposit_coin_info`, `asset_get_withdrawal_records`, `asset_get_withdrawable_amount`, `asset_get_convert_coin_list`, `asset_get_convert_status`, `asset_get_convert_history`, `asset_get_delivery_record`, `asset_get_session_settlement`, `asset_get_exchange_records`, `asset_get_sub_uid`, `asset_get_asset_info`.

### User
`user_get_api_key_information`, `user_get_uid_wallet_type`, `user_get_affiliate_user_info`.

### Spot Margin (UTA)
`spotmargin_get_state`, `spotmargin_get_vip_margin_data`, `spotmargin_get_borrow_records`, `spotmargin_get_interest_records`.

### Earn / Crypto Loan
- Earn (FlexibleSaving / OnChain): `earn_get_product_info(category)`, `earn_get_position(category)`, `earn_get_order_history(category)`. **`category` обязателен** (`FlexibleSaving` или `OnChain`).
- byUSDT token-earn: `earn_get_token_position`, `earn_get_token_orders`.
- Crypto Loan: `loan_get_orders`, `loan_get_repayment_history`, `loan_get_collateral_info`, `loan_get_borrowable_coins`, `loan_get_account_info`, `loan_get_max_borrowable`.

### P2P
`p2p_get_account_info`, `p2p_get_ads_list`, `p2p_get_my_ads`, `p2p_get_ad_info`, `p2p_get_orders`, `p2p_get_pending_orders`, `p2p_get_order_info`, `p2p_get_chat_messages`, `p2p_get_payment_methods`, `p2p_get_counterparty_info`.

### Bybit Card
`card_get_transactions` (history), `card_get_points_balance`, `card_get_points_records`, `card_get_points_tier`.

> Доступно только владельцам Bybit Card. Зависит от региона и KYC. Если карта не выпущена — сервер вернёт graceful `{error: True, ret_code: 10005}` envelope, не упадёт.

### Что НЕ реализовано

**Мутирующие методы (исключены по дизайну):** order placement/amend/cancel, leverage/margin mode switching, position close, set_trading_stop, all transfers, withdrawals, P2P order release/cancel/message, Earn purchase/redeem, loan borrow/repay, convert quote/confirm, card top-up/freeze, ByX publication create/edit/delete.

**Сервисы без публичного V5 REST API:**
- **Bybit Pay** (peer-to-peer) — отдельного `/v5/pay/*` namespace не существует. Единственный связанный endpoint — `/v5/account/pay-info`, реализован как `account_get_pay_info`.
- **ByX (community publications)** — V5 REST endpoints отсутствуют на момент написания. Соответствующий permission scope в API key зарезервирован для будущего использования.

---

## Требования

- **Python 3.10+**
- **uv** — установка: <https://docs.astral.sh/uv/getting-started/installation/>
- **Read-only API-ключ ByBit**

## Получение read-only ключа

1. Открой <https://www.bybit.com/app/user/api-management>
2. **Create New Key → System-generated API Keys → API Transaction**
3. **API Key Permissions: Read-Only** ✅, всё остальное в правах НЕ ставить
4. Scope-чекбоксы: поставь `Unified Trading Account` (раскроет Контракт/Спот/USDC read-only), `Earn`, `Активы → Кошелёк`. P2P / Bybit Pay / Card / ByX — отметь, если будешь их использовать.
5. IP Restrictions: либо свой IP, либо `No IP restriction` (тогда ключ умрёт через 90 дней — для read-only это нормально).
6. Подтверди 2FA → скопируй **API Key** + **API Secret** (secret виден один раз).

## Установка

```bash
git clone https://github.com/<you>/InvestMCPs.git
cd InvestMCPs/ByBitMCP
uv sync
```

## Запуск из Claude Desktop

Конфиг Claude Desktop:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bybit": {
      "command": "/абсолютный/путь/uv",
      "args": [
        "--directory",
        "/абсолютный/путь/InvestMCPs/ByBitMCP",
        "run",
        "bybit-mcp"
      ],
      "env": {
        "BYBIT_API_KEY": "ВАШ_КЛЮЧ",
        "BYBIT_API_SECRET": "ВАШ_СЕКРЕТ"
      }
    }
  }
}
```

Пути обязательно **абсолютные**. Узнать путь к `uv`: `which uv` (macOS/Linux) или `where uv` (Windows). После сохранения — полностью перезапустите Claude Desktop.

### Запуск вручную (для отладки)

```bash
BYBIT_API_KEY=ВАШ BYBIT_API_SECRET=ВАШ uv run bybit-mcp
```

Сервер общается по stdio — JSON-RPC через stdin/stdout, логи в stderr. Ctrl+C для остановки.

## Безопасность

- **Ключ только read-only.** Read-only ключ ByBit не может ни торговать, ни выводить средства, ни переводить между аккаунтами. Но он **видит баланс и историю операций**.
- **`.env` в `.gitignore`.** Никогда не коммить реальный ключ. Шаблон — в `.env.example`.
- Сервер логирует service/method вызовов на stderr; **API Secret в логи не пишется**. В сообщениях ошибок строки `X-BAPI-SIGN: <hex>` и `X-BAPI-API-KEY: <key>` маскируются.
- TLS-валидация включена (стандартный certifi-бандл — у ByBit обычная западная цепочка сертификатов, ничего экзотического).
- Сервер общается **только** с `api.bybit.com` (или testnet). Никаких других внешних запросов.

## Переменные окружения

| Имя | Назначение | Дефолт |
|---|---|---|
| `BYBIT_API_KEY` | API-ключ (обязателен для приватных методов) | — |
| `BYBIT_API_SECRET` | API-секрет (обязателен для приватных методов) | — |
| `BYBIT_TESTNET` | `1` → стучаться в `api-testnet.bybit.com` | `0` |
| `BYBIT_RECV_WINDOW` | окно валидности подписи в мс | `5000` |
| `BYBIT_TIMEOUT` | таймаут HTTP-запроса в секундах | `30` |
| `BYBIT_LOG_LEVEL` | DEBUG / INFO / WARNING / ERROR | `INFO` |
| `BYBIT_API_BASE` | переопределение base URL (только https://) | автодетект |

## Примеры запросов в Claude

- «Какой у меня баланс по USDT и общий equity?»
- «Сколько я заработал/потерял на открытых позициях?»
- «Покажи историю закрытых позиций по BTCUSDT за месяц.»
- «Какие у меня активные ордера?»
- «Что у меня лежит в Earn и какую доходность приносит?»
- «Покажи P2P-ордера за неделю.»
- «Какая funding rate была на BTCUSDT за сутки?»
- «Дай свечи ETHUSDT 4h за последние 7 дней.»

## Известные ограничения

- **Стримы не поддерживаются.** WebSocket-каналы ByBit не реализованы.
- **Доступность не-trading сервисов** (P2P, Card) **зависит от региона/KYC**. Если сервис недоступен на твоём аккаунте — соответствующий tool вернёт `{error: true, ret_code: 10005 ...}`, а не упадёт.
- Поля `pnl` в `account_get_wallet_balance` и `position_get_list` вычисляются на стороне сервера по полям API. Если ByBit вернул только частичные данные (например, нет markPrice для какой-то позиции) — соответствующие поля будут `null`.
- **Понять коды ошибок ByBit.** Каждый вызов возвращает `retCode`; описания всех кодов — в [официальном reference](https://bybit-exchange.github.io/docs/v5/error). Если видишь `retCode 10003` (API key invalid) — проверь scope; `10004` (sign error) — пересинхронизируй часы; `10005` (permission denied) — сервис недоступен для твоего региона/KYC; `10006` (rate limit) — подожди.
- **После переименования родительской папки** (например, `Инвестиции/TinkoffMCP/` → `Инвестиции/InvestMCPs/`) виртуальное окружение `.venv` ломается, потому что `pyvenv.cfg` и `uv.lock` содержат абсолютные пути. Лечится в один заход: `rm -rf .venv && uv sync`.

## Архитектура (коротко)

- `src/bybit_mcp/server.py` — FastMCP-приложение и точка входа.
- `src/bybit_mcp/client.py` — обёртка над `httpx.Client`, HMAC-подпись, тайм-ауты, обработка `retCode`.
- `src/bybit_mcp/serialize.py` — конверсия чисел (ByBit отдаёт строки) и Quotation-подобных значений в `Decimal`-строки.
- `src/bybit_mcp/_runtime.py` — `call_api`, который оборачивает ошибки в JSON-envelope.
- `src/bybit_mcp/tools/*.py` — модули по сервисам: `market.py`, `account.py`, `position.py`, `order.py`, `asset.py`, `user.py`, `spotmargin.py`, `earn.py`, `p2p.py`, `card.py`.

## Contributing

Pull-request'ы приветствуются. Перед PR:

```bash
uv sync --group dev
uv run ruff format src/
uv run ruff check src/
uv run bybit-mcp     # сервер должен подняться и НЕ писать ничего в stdout
```

## Лицензия

[MIT](LICENSE).
