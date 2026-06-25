# Payments — Асинхронный сервис обработки платежей

Событийно-ориентированный микросервис обработки платежей на Clean Architecture с паттерном ports-and-adapters.

## Архитектура

```
Клиент (HTTP + API-Key)
    │ POST /v1/payments
    ▼
┌──────────────────┐          ┌─────────────┐          ┌──────────────────┐
│  web (FastAPI)   │  outbox  │   RabbitMQ  │  прием   │     consumer     │
│  relay           │ ───────▶ │  (брокер)   │ ◀─────── │  consumer-relay  │
│  listener        │          │             │          │                  │
└──────┬───────────┘          └──────┬──────┘          └──────┬───────────┘
       │ PostgreSQL                   │                        │ SQLite
       │ (платежи + outbox)           │                        │ (дедупликация + outbox)
       │                              │                        │
       ◀────── payments.processed ────┘                        │
       │ (listener обновляет статус +                          │
       │  отправляет webhook)                                  │
       ▼                                                       │
     Webhook URL                                                │
```

### Поток данных

1. **POST /v1/payments** — создание платежа (идемпотентность через `Idempotency-Key`), сохранение в PostgreSQL, событие пишется в outbox
2. **relay** — читает outbox, публикует `payments.new` в RabbitMQ
3. **consumer** — получает `payments.new`, эмулирует обработку (задержка 2–5 с, 90% успех), пишет результат в SQLite outbox
4. **consumer-relay** — читает SQLite outbox, публикует `payments.processed` в RabbitMQ
5. **listener** — получает `payments.processed`, обновляет статус платежа в PostgreSQL, отправляет webhook (3 попытки с экспоненциальной задержкой)

### Структура проекта

```
payments/
├── src/payments/          # Основной пакет API
│   ├── domain/            # Сущности, value objects, доменные события
│   ├── application/       # Сценарии (handlers), порты, общие исключения
│   ├── infrastructure/    # Адаптеры (БД, AMQP, webhook), persistence tables
│   ├── presentation/      # HTTP и AMQP роуты, схемы, обработчики ошибок
│   └── main/              # Точки входа (web, relay, listener), DI, конфиг
├── packages/consumer/     # Пакет consumer (workspace member)
│   └── src/consumer/
│       ├── application/   # ProcessPaymentHandler, порты
│       ├── infrastructure/# Адаптер SQLite, consumer outbox relay
│       ├── presentation/  # AMQP подписчик
│       └── main/          # Точки входа, DI, конфиг
├── tests/                 # 27 тестов (модульные, интеграционные, AMQP)
├── docker/Dockerfile      # Multi-stage uv сборка
├── docker-compose.yml     # 8 сервисов
├── pyproject.toml         # Корень workspace (uv)
└── Makefile
```

### Слои Clean Architecture

| Слой | Ответственность |
|---|---|
| **domain** | Сущность `Payment`, `PaymentId`, `Currency`, `PaymentStatus`, доменные события |
| **application** | `CreatePaymentHandler`, `GetPaymentHandler`, `UpdatePaymentStatusHandler`, порты (протоколы) |
| **infrastructure** | Адаптеры PostgreSQL/aiosqlite, RabbitMQ publisher, outbox relay (FOR UPDATE SKIP LOCKED), HttpxWebhookClient |
| **presentation** | FastAPI роуты (`/v1/payments`), AMQP подписчики (`payments.new`, `payments.processed`), DLQ-обработчики |
| **main** | Точки входа, DI-контейнер Dishka, конфиг (pydantic-settings) |

## Технологический стек

- **Python** 3.14+
- **FastAPI** — HTTP API
- **FastStream** — AMQP (RabbitMQ) консьюмеры/паблишеры
- **SQLAlchemy 2.0** (async) — ORM для PostgreSQL
- **aiosqlite** — локальное хранилище consumer (дедупликация + outbox)
- **Alembic** — миграции базы данных
- **Dishka** — внедрение зависимостей (с интеграцией `dishka-faststream`)
- **Pydantic v2 + pydantic-settings** — валидация и конфигурация
- **httpx** — асинхронный webhook-клиент
- **uv** — пакетный менеджер и оркестратор workspace

## Быстрый старт

### Требования

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Docker и docker-compose

### Настройка

```bash
# Установка зависимостей
uv sync

# Создать .env файл (при необходимости отредактировать)
cp .env.example .env

# Запуск миграций
uv run alembic upgrade head
```

### Переменные окружения (`.env`)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `APP_API_KEY` | `secret-api-key` | API-ключ для заголовка X-API-Key |
| `POSTGRES_HOST` | `localhost` | Хост PostgreSQL |
| `POSTGRES_PORT` | `5432` | Порт PostgreSQL |
| `POSTGRES_DB` | `payments` | Имя базы данных |
| `POSTGRES_USER` | `postgres` | Пользователь БД |
| `POSTGRES_PASSWORD` | `postgres` | Пароль БД |
| `RABBIT_HOST` | `localhost` | Хост RabbitMQ |
| `RABBIT_PORT` | `5672` | Порт RabbitMQ |
| `RABBIT_USER` | `guest` | Пользователь RabbitMQ |
| `RABBIT_PASSWORD` | `guest` | Пароль RabbitMQ |

## Запуск

### Docker Compose (все сервисы)

```bash
docker-compose up -d
```

Запускает 8 сервисов: postgres, rabbitmq, migrator, web, relay, listener, consumer, consumer-relay.

### Запуск сервисов по отдельности

```bash
# Web API (порт 8000)
uv run python -m payments.main.web

# Outbox relay
uv run python -m payments.main.relay

# Listener (AMQP-консьюмер обработанных платежей)
uv run python -m payments.main.listener

# Consumer (AMQP-подписчик + обработчик)
uv run python -m consumer.main

# Consumer outbox relay
uv run python -m consumer.main.relay
```

## API

### Аутентификация

Все эндпоинты требуют заголовок `X-API-Key`. По умолчанию: `secret-api-key`.

### Эндпоинты

#### Создание платежа

```http
POST /v1/payments/
Content-Type: application/json
X-API-Key: secret-api-key
Idempotency-Key: <unique-key>
```

```json
{
  "amount": "100.50",
  "currency": "USD",
  "description": "Заказ #12345",
  "webhook_url": "https://example.com/webhook",
  "metadata": {"order_id": "12345"}
}
```

Ответ `202 Accepted`:
```json
{
  "payment_id": "019b8e5e-...",
  "status": "pending",
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### Получение платежа

```http
GET /v1/payments/{payment_id}
X-API-Key: secret-api-key
```

#### Проверка здоровья

```http
GET /v1/health
```

### Идемпотентность

Повторный запрос с тем же `Idempotency-Key` возвращает существующий платёж вместо создания дубликата. Конфликт возвращает `409`.

### Webhook-уведомления

При завершении обработки платежа сервис отправляет POST на `webhook_url`:
```json
{
  "payment_id": "019b8e5e-...",
  "status": "completed"
}
```
Повторы: 3 попытки с экспоненциальной задержкой.

## Тестирование

```bash
# Все тесты (требуются PostgreSQL и RabbitMQ)
uv run pytest -q

# Отдельные наборы тестов
uv run pytest tests/service/test_handlers.py -q
uv run pytest tests/service/test_payments_api.py -q
uv run pytest tests/service/test_amqp.py -q
uv run pytest tests/unit/ -q
```

### Линтинг и проверка типов

```bash
uv run ruff check .
uv run mypy src/ packages/ tests/
```

### Makefile

```bash
make lint      # ruff check
make typecheck # mypy
make test      # pytest
```

## Ключевые архитектурные решения

| Решение | Обоснование |
|---|---|
| **Паттерн Outbox** | Гарантирует доставку at-least-once из БД в брокер; relay читает с `FOR UPDATE SKIP LOCKED` |
| **Нет статуса DEAD в outbox** | События остаются `PENDING`; экспоненциальная задержка ограничивает повторы естественным образом — без dead-letter в БД |
| **Consumer с собственной SQLite** | У consumer своя БД (дедупликация + outbox) — нет доступа к PostgreSQL основного сервиса |
| **Идемпотентность** | Заголовок `Idempotency-Key` при создании; unique constraint на (key, gateway) |
| **Оптимистичная конкурентность** | `FOR UPDATE SKIP LOCKED` в PostgreSQL, `BEGIN IMMEDIATE` в SQLite |
