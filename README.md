# Nova Freedom VPN

Telegram-бот для управления персональным VPN-сервисом на базе VLESS+Reality.

## Возможности

- Регистрация пользователей с одобрением администратора
- Создание VPN-конфигураций (до 3 устройств на пользователя)
- Несколько протоколов: основной Reality, Google SNI bypass для мобильных, CDN fallback
- Админ-панель: управление пользователями, статистика, рассылка
- Subscription server для автоимпорта в VPN-клиенты
- Интеграция с AdGuard Home (блокировка рекламы через DNS)

## Архитектура

```
Telegram Bot (aiogram 3)
    ↓
UserService → HiddifyManager (API)
    ↓                    ↓
SQLite DB         Hiddify Panel (Xray)
                         ↓
              XrayConfigManager → standalone Xray Reality

Subscription Server (:8888) → base64-encoded VLESS configs
```

### Протоколы

| Протокол | Порт | SNI | Назначение |
|----------|------|-----|------------|
| VLESS+Reality (TCP) | 8443 | addons.mozilla.org | Основной |
| VLESS+Reality (TCP) | 443 | dl.google.com | Обход whitelist мобильных операторов |
| VLESS+Reality (gRPC) | 2053 | www.google.com | Fallback для мобильных |
| VLESS+XHTTP (CDN) | 443 | через Cloudflare | Резервный |

## Требования

- VPS с Ubuntu 22.04+ (рекомендуется Европа: NL, DE)
- Python 3.11+
- Telegram Bot Token (от [@BotFather](https://t.me/BotFather))
- Свой Telegram ID (от [@userinfobot](https://t.me/userinfobot))

## Установка

### 1. Установить Hiddify Manager

```bash
sudo bash -c "$(curl -Lfo- https://raw.githubusercontent.com/hiddify/Hiddify-Manager/main/common/download.sh)"
```

После установки:
- Откройте панель Hiddify в браузере
- Настройте домен (или используйте IP)
- В настройках включите Reality inbound
- Скопируйте API URL и API Key из панели администратора

### 2. Установить standalone Xray Reality (порт 8443)

```bash
# Скачать Xray
mkdir -p /opt/xray-reality
cd /opt/xray-reality
wget https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip
unzip Xray-linux-64.zip
chmod +x xray

# Сгенерировать X25519 ключи
./xray x25519
# Вывод:
#   Private key: <СОХРАНИТЕ — для config.json>
#   Public key:  <СОХРАНИТЕ — для .env>

# Скопировать конфиг из примера
cp /opt/nova-vpn/examples/xray-config.example.json /opt/xray-reality/config.json
# Отредактировать: вставить privateKey
nano /opt/xray-reality/config.json

# Установить systemd сервис
cp /opt/nova-vpn/examples/xray-reality.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now xray-reality
```

### 3. Настроить HAProxy (опционально, для Google SNI bypass)

Нужно, если хотите обходить whitelist мобильных операторов через dl.google.com SNI на порту 443.

```bash
apt install haproxy
# Добавить конфигурацию из examples/haproxy-reality.cfg
nano /etc/haproxy/haproxy.cfg
systemctl restart haproxy
```

### 4. Развернуть бота

```bash
# Клонировать репозиторий
git clone https://github.com/vonavikon/Nova-Freedom-VPN.git /opt/nova-vpn
cd /opt/nova-vpn

# Установить зависимости
pip install -r requirements.txt

# Создать .env из примера
cp .env.example .env
nano .env
# Заполнить: BOT_TOKEN, ADMIN_IDS, HIDDIFY_API_URL, HIDDIFY_API_KEY,
#            REALITY_HOST, REALITY_PUBLIC_KEY и остальное

# Создать директории
mkdir -p /opt/nova-vpn/data

# Установить systemd сервис
cp examples/nova-vpn-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now nova-vpn-bot

# Проверить
systemctl status nova-vpn-bot
journalctl -u nova-vpn-bot -f
```

### Или через Docker

```bash
cp .env.example .env
nano .env  # заполнить переменные
docker-compose up -d
```

### Firewall

Subscription server слушает порт 8888. Если бот и Xray на одном сервере — закройте порт извне:

```bash
# UFW
ufw deny 8888/tcp

# Или iptables
iptables -A INPUT -p tcp --dport 8888 -s !127.0.0.1 -j DROP
```

Бот подключается к Xray через localhost, внешний доступ к 8888 не нужен.

## Конфигурация (.env)

Все переменные описаны в `.env.example`. Основные:

| Переменная | Обязательная | Описание |
|-----------|:---:|-----------|
| `BOT_TOKEN` | да | Токен Telegram-бота |
| `ADMIN_IDS` | да | Telegram ID администраторов через запятую |
| `HIDDIFY_API_URL` | да | URL API Hiddify (например `http://127.0.0.1:9000/your_path/api/v2/admin`) |
| `HIDDIFY_API_KEY` | да | API ключ Hiddify |
| `REALITY_HOST` | да | IP вашего сервера |
| `REALITY_PUBLIC_KEY` | да | X25519 public key (из `xray x25519`) |
| `REALITY_PORT` | нет | Порт Reality (по умолчанию 8443) |
| `REALITY_SNI` | нет | SNI для маскировки (по умолчанию `addons.mozilla.org`) |
| `BYPASS_HOST` | нет | IP для Google SNI bypass |
| `BYPASS_DL_PUBLIC_KEY` | нет | Public key для dl.google.com inbound |
| `BYPASS_GRPC_PUBLIC_KEY` | нет | Public key для gRPC inbound |

## Рекомендуемые VPN-клиенты

| Платформа | Клиент |
|-----------|--------|
| iOS | [VPnet](https://apps.apple.com/ru/app/vpnet/id6756558545), [V2Box](https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690) |
| Android | [VPnet](https://play.google.com/store/apps/details?id=com.gmm.vpnet.client), [V2Box](https://play.google.com/store/apps/details?id=com.v2box.client) |
| Windows/Mac | [Hiddify](https://hiddify.com/) |

Пользователи получают ссылку подписки через бота. Вставить в клиент: Добавить подписку → Вставить URL → Обновить.

## Структура проекта

```
bot/
├── main.py              # Точка входа
├── config.py            # Конфигурация (env)
├── database.py          # SQLite
├── texts.py             # Все тексты бота
├── handlers/
│   ├── user_handlers.py # Пользовательские команды
│   └── admin_handlers.py# Админ-панель
├── services/
│   ├── user_service.py  # Бизнес-логика
│   ├── hiddify_manager.py # Hiddify API + Reality конфиги
│   ├── notification_service.py
│   ├── subscription_server.py # Subscription HTTP server
│   └── xray_config_manager.py # Синхронизация клиентов в Xray
├── keyboards/
│   ├── inline.py
│   └── reply.py
└── tests/
examples/
├── xray-config.example.json  # Шаблон конфига Xray Reality
├── xray-reality.service       # systemd unit для Xray
├── nova-vpn-bot.service       # systemd unit для бота
└── haproxy-reality.cfg        # HAProxy для Google SNI bypass
scripts/
├── vpn_healthcheck.sh         # Мониторинг VPN
├── client_test.sh             # Клиентские тесты
└── cloudflare_check.sh        # Проверка CDN
```

## Диагностика

```bash
# Статус сервисов
systemctl status xray-reality nova-vpn-bot

# Логи бота
journalctl -u nova-vpn-bot -n 50 --no-pager

# Проверить порты
ss -tlnp | grep -E '8443|443|8888'

# Healthcheck
bash scripts/vpn_healthcheck.sh

# Клиентский тест (запускать с включённым VPN)
bash scripts/client_test.sh
```

## Если Reality заблокирован

1. Сменить SNI в `.env` (`REALITY_SNI`) и перезапустить бота + Xray
2. Перенести на высокий порт (47000+), обновить firewall
3. Использовать Google SNI bypass (dl.google.com, порт 443)

## Лицензия

MIT — см. [LICENSE](LICENSE).
