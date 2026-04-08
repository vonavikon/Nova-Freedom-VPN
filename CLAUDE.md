# Nova Freedom VPN — Agent Instructions

> This file helps AI coding assistants understand the project.

## Overview

**Nova Freedom VPN** — Telegram bot for managing a personal VPN service (VLESS+Reality).

## Architecture

```
Telegram Bot (aiogram 3)
    ↓
UserService → HiddifyManager (API)
    ↓                    ↓
SQLite DB         Hiddify Panel (Xray)
                         ↓
              XrayConfigManager → config.json

Subscription Server (:8888) → base64-encoded VLESS configs
```

## Configuration

All secrets and server-specific data are in `.env` (see `.env.example`).

## Project Structure

```
bot/
├── main.py              # Entry point
├── config.py            # Configuration (env vars)
├── database.py          # SQLite
├── texts.py             # All bot texts
├── handlers/
│   ├── user_handlers.py # User commands
│   └── admin_handlers.py# Admin panel
├── services/
│   ├── user_service.py  # Business logic
│   ├── hiddify_manager.py # Hiddify API + Reality configs
│   ├── notification_service.py
│   ├── subscription_server.py # HTTP subscriptions
│   └── xray_config_manager.py # Xray config sync
├── keyboards/
│   ├── inline.py
│   └── reply.py
└── tests/
```

## Key Commands

```bash
# Run bot
python bot/main.py

# Run tests
pytest bot/tests/

# Docker
docker-compose up -d
```
