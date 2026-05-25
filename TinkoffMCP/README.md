# Tinkoff MCP — read-only T-Invest для Claude

Неофициальный MCP-сервер для **T-Invest API** (T-Bank / Тинькофф Инвестиции). Подключается к Claude Desktop (или любому MCP-клиенту) и даёт LLM-агенту читать ваш брокерский счёт: портфель, P&L, позиции, операции, дивиденды, заявки, а также рыночные данные.

> ⚠️ **Дисклеймер.** Проект **неофициальный**, никак не связан с АО «Т-Банк» и не одобрен им. Сервер работает **только на чтение**: вся торговая часть API (postOrder, cancelOrder, replaceOrder, postStopOrder, cancelStopOrder) и Sandbox-сервис **не реализованы и не импортируются** — выпускайте read-only токен, и хуже всего, что может случиться, — кто-то узнает ваш баланс.

Под капотом — прямые REST-вызовы к `https://invest-public-api.tbank.ru/rest/...` через `httpx`. SDK `tinkoff-investments` намеренно не используется (на момент создания проекта пакет на PyPI в карантине), поэтому стек минимален: только `mcp[cli]` и `httpx`.

---

## Что умеет

58 инструментов, по одному на каждый read-метод API. Сгруппированы по сервисам:

### UsersService — счета и тариф
- `users_get_accounts` — список брокерских счетов (источник `account_id` для всего остального).
- `users_get_info` — статус квал/неквала, лимит на streaming-подключения, премиум.
- `users_get_margin_attributes` — маржинальные показатели по счёту.
- `users_get_user_tariff` — текущий тариф и квоты на методы/стримы.

### OperationsService — деньги, P&L, история
- `operations_get_portfolio` — портфель по счёту. **Возвращает дополнительно поле `pnl` с уже посчитанными метриками**: общая стоимость, общая доходность (абсолют + %), разбивка по типам активов, и по каждой позиции — количество, средняя цена покупки, текущая цена, текущая стоимость и P&L (абсолютный + %).
- `operations_get_positions` — позиции (деньги, ценные бумаги, фьючерсы, опционы, заблокированные средства).
- `operations_get_withdraw_limits` — **сколько свободных денег можно вывести** по валютам.
- `operations_get_operations` — история операций по счёту с фильтрами (период, статус, FIGI).
- `operations_get_operations_by_cursor` — пагинированная история (для больших периодов).
- `operations_get_dividends_foreign_issuer` — отчёт по дивидендам иностранных эмитентов (генерация и получение).
- `operations_get_broker_report` — брокерский отчёт (генерация и получение).

### InstrumentsService — справочники инструментов
Списки: `instruments_shares`, `instruments_bonds`, `instruments_etfs`, `instruments_currencies`, `instruments_futures`, `instruments_options`, `instruments_options_by`, `instruments_indicatives`. По одному инструменту: `instruments_share_by`, `instruments_bond_by`, `instruments_etf_by`, `instruments_currency_by`, `instruments_future_by`, `instruments_option_by`, `instruments_get_instrument_by`. Поиск: `instruments_find_instrument`. Расписание торгов: `instruments_trading_schedules`. Справочные: `instruments_get_countries`, `instruments_get_brands`, `instruments_get_brand_by`. Дивиденды и купоны: `instruments_get_dividends`, `instruments_get_bond_coupons`, `instruments_get_bond_events`, `instruments_get_accrued_interests`. Активы: `instruments_get_assets`, `instruments_get_asset_by`, `instruments_get_asset_fundamentals`, `instruments_get_asset_reports`. Аналитика: `instruments_get_consensus_forecasts`, `instruments_get_forecast_by`. Прочее: `instruments_get_favorites`, `instruments_get_risk_rates`.

### MarketDataService — рыночные данные
- `marketdata_get_candles` — свечи по инструменту за период.
- `marketdata_get_last_prices` — последние цены по списку инструментов.
- `marketdata_get_close_prices` — цены закрытия предыдущей сессии.
- `marketdata_get_order_book` — стакан.
- `marketdata_get_trading_status` / `marketdata_get_trading_statuses` — статус торгов.
- `marketdata_get_last_trades` — обезличенные сделки.
- `marketdata_get_tech_analysis` — технические индикаторы.

### OrdersService — заявки (только чтение)
- `orders_get_orders` — открытые заявки по счёту.
- `orders_get_order_state` — состояние конкретной заявки.
- `orders_get_max_lots` — максимально доступное количество лотов.
- `orders_get_order_price` — расчёт цены/комиссии заявки.

### StopOrdersService — стоп-заявки (только чтение)
- `stoporders_get_stop_orders` — активные стоп-заявки.

### SignalService — сигналы стратегий
- `signals_get_strategies` — список стратегий.
- `signals_get_signals` — сигналы по стратегиям.

> Мутирующие методы (`PostOrder`, `CancelOrder`, `ReplaceOrder`, `PostOrderAsync`, `PostStopOrder`, `CancelStopOrder`) и Sandbox-сервис **отсутствуют по дизайну**.

---

## Требования

- **Python 3.10+**
- **uv** — установка: <https://docs.astral.sh/uv/getting-started/installation/>
- **Read-only токен T-Invest** — см. ниже
- Желательно подключение к российским сертификатам (Russian Trusted Root CA уже включён в репозиторий, подцепляется автоматически)

## Получение read-only токена

1. Откройте <https://www.tbank.ru/invest/settings/api/>
2. Нажмите **Создать токен** → дайте имя, например `claude-readonly`
3. **Снимите все галочки, кроме «Только чтение»**. Если оставите «Торговля», у этого токена будет право на покупки и продажи через API. Нам это не нужно — сервер read-only, пусть и токен будет таким же.
4. Скопируйте токен — увидеть его второй раз нельзя.

> Все методы из `OrdersService` / `StopOrdersService` в этом проекте — read-only (`GetOrders`, `GetOrderState`, `GetStopOrders`). С read-only токеном они работают, торговых не пытаются.

## Установка

```bash
git clone https://github.com/SadLiter/TinkoffMCP.git
cd TinkoffMCP
uv sync
```

Это создаст `.venv` с `mcp[cli]` и `httpx`. Бандл `certs/russian_trusted_ca.pem` уже лежит в репозитории — он публичный (корневой и промежуточный CA Минцифры).

## Запуск из Claude Desktop

Откройте файл конфига Claude Desktop:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Добавьте секцию `mcpServers`:

```json
{
  "mcpServers": {
    "tinkoff": {
      "command": "/абсолютный/путь/uv",
      "args": [
        "--directory",
        "/абсолютный/путь/TinkoffMCP",
        "run",
        "tinkoff-mcp"
      ],
      "env": {
        "INVEST_TOKEN": "t.ВАШ_READ_ONLY_ТОКЕН"
      }
    }
  }
}
```

Пути обязательно **абсолютные**. Узнать путь к `uv`: `which uv` (macOS/Linux) или `where uv` (Windows). После сохранения — полностью перезапустите Claude Desktop.

### Запуск вручную (для отладки)

```bash
INVEST_TOKEN="t.ВАШ_ТОКЕН" uv run tinkoff-mcp
```

Сервер общается по stdio — в терминале вы увидите только логи на stderr (JSON-RPC идёт через stdin/stdout и не выводится на экран). Чтобы прервать — Ctrl+C.

## Безопасность

- **Токен — только read-only.** Это не строгая рекомендация, это компромисс между удобством и худшим возможным сценарием. Read-only токен не может торговать, но **видит историю операций**: что/когда/по какой цене вы покупали, остатки по счёту. Это всё равно чувствительные данные — не светите токен и не запускайте сервер на чужом железе.
- **`.env` — в `.gitignore`.** Никогда не коммитьте реальный токен. Шаблон лежит в `.env.example`.
- Сервер логирует имя метода и длину ответа на stderr (`TBANK_LOG_LEVEL=DEBUG` — добавить хедеры запроса). Сам токен в логи не пишется.
- TLS-валидация включена. Сертификат T-Bank подписан Russian Trusted Root CA — бандл лежит в `certs/`. Если хотите свой — задайте `TBANK_CA_BUNDLE=/path/to/your.pem`.
- Сервер общается **только** с `invest-public-api.tbank.ru`. Никаких других внешних запросов.

## Переменные окружения

| Имя | Назначение | Дефолт |
|---|---|---|
| `INVEST_TOKEN` | T-Invest API-токен (обязателен) | — |
| `TBANK_CA_BUNDLE` | Путь к CA bundle, если нужен свой | бандл из `certs/` |
| `TBANK_TIMEOUT` | Таймаут HTTP-запроса в секундах | `30` |
| `TBANK_LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR` | `INFO` |
| `TBANK_API_BASE` | Базовый URL REST API | `https://invest-public-api.tbank.ru/rest` |

## Примеры запросов в Claude

После подключения сервера, в Claude Desktop можно писать на естественном языке:

- «Покажи мой портфель и общий P&L по каждой позиции.»
- «Сколько у меня свободных рублей и долларов?»
- «Во сколько мне обошлась позиция по SMLT и где она сейчас?»
- «Какие дивиденды по SBER ожидаются в ближайшие месяцы?»
- «Дай свечи по YNDX за последний месяц, 1d.»
- «Что у меня по операциям за май?»
- «Покажи открытые заявки и стоп-заявки.»
- «Найди инструмент по тикеру MOEX.»

Claude автоматически выберет нужный MCP-инструмент, дернёт API через сервер и сформирует человекочитаемый ответ.

## Известные ограничения

- **Стримы не поддерживаются.** API имеет `MarketDataStream`, `OperationsStream`, `OrdersStream` — это gRPC bidirectional streams, которые в REST-обвязке делать тяжело и которые плохо ложатся на парадигму tool-вызова в MCP. Если нужны live-обновления — открывайте Issue.
- **Sandbox API не реализован.** Для боевой работы он не нужен; если хочется потренироваться без реальных денег — добавлю.
- Некоторые методы (например, `GetBrokerReport`, `GetDividendsForeignIssuerReport`) асинхронные двухстадийные — сначала «сгенерируй», потом «получи готовое». Сервер поддерживает обе стадии, но удобнее запрашивать после того, как T-Bank уведомил о готовности.
- Поле `pnl` в `operations_get_portfolio` считается на стороне сервера и опирается на поля API `averagePositionPrice` и `currentPrice`. Если у позиции нет средней цены (например, бумага куплена до подключения API или в результате корпоративных действий), P&L будет посчитан по `expectedYield` из API.

## Архитектура (коротко)

- `src/tinkoff_mcp/server.py` — FastMCP-приложение и точка входа (`main`).
- `src/tinkoff_mcp/client.py` — обёртка над `httpx.Client`, авторизация, тайм-ауты, TLS-CA, обработка ошибок API.
- `src/tinkoff_mcp/serialize.py` — конверсия Quotation/MoneyValue → `Decimal`-строка, datetime → ISO 8601. Все числовые величины приходят клиенту как строки, чтобы не терять точность через float.
- `src/tinkoff_mcp/tools/*.py` — модули по сервисам (`users.py`, `operations.py`, `instruments.py`, `marketdata.py`, `orders.py`, `stoporders.py`, `signals.py`). Каждый инструмент — функция, обёрнутая `@mcp.tool()`.
- `certs/russian_trusted_ca.pem` — публичный Root + Sub CA Минцифры РФ (требуется для TLS-валидации `*.tbank.ru`).

## Лицензия

[MIT](LICENSE).

## Contributing

Pull-request'ы приветствуются. Перед PR:

```bash
uv sync --group dev          # установить ruff
uv run ruff format src/      # отформатировать
uv run ruff check src/ scripts/   # линт
uv run tinkoff-mcp           # сервер должен подняться и НЕ писать ничего в stdout
```

Конфиг линтера и форматтера — в `[tool.ruff]` секции `pyproject.toml`. Целевая версия Python — `py310`, длина строки — 100.
