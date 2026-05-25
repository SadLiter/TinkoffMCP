# Russian Trusted CA bundle

`russian_trusted_ca.pem` содержит два публичных X.509-сертификата Минцифры РФ, которые подписывают цепочку `*.tbank.ru`:

| Subject | Issuer | Not After |
|---|---|---|
| `CN=Russian Trusted Root CA` (self-signed) | self | 2032-02-27 |
| `CN=Russian Trusted Sub CA` | Russian Trusted Root CA | 2027-03-06 |

Источник — официальный сайт Госуслуг:

- https://gu-st.ru/content/Other/doc/russian_trusted_root_ca.cer
- https://gu-st.ru/content/Other/doc/russian_trusted_sub_ca.cer

Сертификаты публичные, никакой приватной информации не содержат. Распространяются вместе с инсталляторами «Госуслуги/КриптоПро Российский Trusted Root CA».

## Зачем

Сертификат `*.tbank.ru` подписан этими CA. В стандартный `certifi`/системный trust store на macOS/Linux/Windows они не входят. Без них `httpx` (и любой другой HTTPS-клиент) откажется устанавливать TLS-соединение с `invest-public-api.tbank.ru`.

## Обновление

Sub CA истекает 2027-03-06. Когда T-Bank выпустит новый промежуточный CA или просто захочется освежить бандл:

```bash
./scripts/refresh-ca.sh
```

или вручную:

```bash
curl -sL https://gu-st.ru/content/Other/doc/russian_trusted_root_ca.cer \
  | openssl x509 -inform DER -out /tmp/root.pem
curl -sL https://gu-st.ru/content/Other/doc/russian_trusted_sub_ca.cer \
  | openssl x509 -inform DER -out /tmp/sub.pem
{ cat /tmp/root.pem; echo; cat /tmp/sub.pem; } > certs/russian_trusted_ca.pem
```

После обновления — проверка:

```bash
python3 -c "import ssl; print(ssl.create_default_context(cafile='certs/russian_trusted_ca.pem').cert_store_stats())"
# Должно быть {'x509': 2, 'crl': 0, 'x509_ca': 2}
```

## Использование своего bundle

Если вы уже добавили эти CA в системный trust store или хотите указать свой кастомный bundle, задайте переменную окружения:

```bash
export TBANK_CA_BUNDLE=/path/to/your.pem
```

Сервер возьмёт её вместо встроенного бандла.
