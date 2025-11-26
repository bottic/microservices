# API Overview

Документация по доступным HTTP-ручкам для сервисов монорепозитория.

## Auth Service

Базовый префикс: зависит от окружения (по умолчанию сервис разворачивается на своём контейнере), все пути ниже начинаются с `/`.

### Здоровье

| Метод | Путь | Описание |
| --- | --- | --- |
| GET | `/health` | Проверка статуса сервиса. |

**Пример запроса (curl)**

```sh
curl -X GET http://localhost:8000/health
```

### Регистрация, вход, пароль

| Метод | Путь | Тело запроса | Описание | Ответ |
| --- | --- | --- | --- | --- |
| POST | `/auth/register` | `{ "email": "user@example.com", "password": "string" }` | Создаёт нового пользователя; валидирует уникальность email. | 201 с объектом пользователя `{ "id": "UUID", "email": "string" }`. Ошибка 400 если email уже существует. |
| POST | `/auth/login` | `{ "email": "user@example.com", "password": "string" }` | Проверяет учетные данные, выдаёт access и ставит refresh в HttpOnly cookie. | 200 с `{ "access_token": "<jwt>", "token_type": "bearer" }` и Set-Cookie `refresh_token=<jwt>; HttpOnly`. Ошибка 401 при неверных данных. |
| POST | `/auth/refresh` | (пустое тело) | Обновляет access-токен по заголовку `Authorization: Bearer <access_token>`; также обновляет refresh в HttpOnly cookie. | 200 с `{ "access_token": "<jwt>", "token_type": "bearer" }` и обновлённым Set-Cookie `refresh_token=<jwt>; HttpOnly`. Ошибка 401 при неверном/просроченном токене. |
| POST | `/auth/change-password` | `{ "email": "user@example.com", "password": "old", "newPassword": "new" }` | Проверяет старый пароль и обновляет на новый, выдаёт свежие access+refresh. | 200 с `{ "access_token": "<jwt>", "token_type": "bearer" }` и Set-Cookie `refresh_token=<jwt>; HttpOnly`. Ошибка 401 при неверных данных. |
| POST | `/auth/logout` | (пустое тело) | Требует заголовок `Authorization: Bearer <access_token>`, удаляет refresh cookie. | 200 `{ "detail": "Logged out" }`. |

**Примеры запросов (curl)**

```sh
# Регистрация
curl -X POST http://192.168.1.8:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"@exam1ple.com","password":"P@ssw0rd"}'
```

```sh
# Регистрация
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@exam1pl.com","password":"P@ssw0rd"}'
```

```sh
# 1) логин
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@exam1ple.com","password":"P@ssw0rd"}'

# 2) обновление access по заголовку Authorization (подставьте токен из шага 1)
ACCESS_TOKEN="<access_token_from_login>"
curl -i -X POST http://localhost:8000/auth/refresh \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"

```

```sh
curl -i -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"

```

```sh
# 1) логин, сохранить куку
curl -i -c backend/cookies.txt -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@exam1ple.com","password":"P@ssw0rd"}'
# Смена пароля, используя ту же куку (refresh обновится)


```

```sh
curl -i -b backend/cookies.txt -X POST http://localhost:8000/auth/change-password \
  -H "Content-Type: application/json" \
  -d '{"email":"user@exam1ple.com","password":"P@ssw0rd","newPassword":"N3wP@ss"}'


```

```sh
# Логаут: удаляет refresh cookie
curl -i -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

```sh
# Просмотр логов аутх сервиса
kubectl logs deploy/auth -n microservices
```

## Gateway Service

Gateway проксирует запросы к другим сервисам и предоставляет защищённые ручки.

### Публичные ручки

| Метод | Путь | Описание | Проксирует |
| --- | --- | --- | --- |
| GET | `/health` | Проверка статуса gateway. | — |
| POST | `/auth/login` | Пробрасывает тело запроса в Auth Service `/auth/login`; контент-тип сохраняется. | Auth Service |
| POST | `/auth/refresh` | Пробрасывает тело и заголовок Authorization в Auth Service `/auth/refresh`; возвращает Set-Cookie. | Auth Service |
| POST | `/auth/register` | Пробрасывает тело запроса в Auth Service `/auth/register`. | Auth Service |
| POST | `/auth/change-password` | Пробрасывает тело и cookie в Auth Service `/auth/change-password`. | Auth Service |
| POST | `/auth/logout` | Пробрасывает заголовок Authorization в Auth Service `/auth/logout`. | Auth Service |
| GET | `/catalog/events` | Возвращает список событий, перенося все query-параметры как есть. | Catalog Service |
| GET/HEAD | `/scraperCatalog/photos/{path}` | Отдаёт постеры, проксируя статику scraperCatalog. | ScraperCatalog Service |

### Защищённые ручки

Для обращения к защищённым ручкам требуется заголовок `Authorization: Bearer <access_token>` с access-токеном, полученным из Auth Service.

| Метод | Путь | Описание | Ответ |
| --- | --- | --- | --- |
| GET | `/me/ping` | Тестовая ручка аутентификации; доступна только при валидном JWT. | `{ "message": "pong", "user_id": "<sub из токена>" }` или 401 при отсутствии/некорректном токене. |

**Пример запроса (curl)**

```sh
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTQ0MWRjMS1lNGRhLTQxOGQtYmFjZC0xN2JlN2JjYTJhNjUiLCJpYXQiOjE3NjM4MTgwMzMsImV4cCI6MTc2MzgxODkzM30.acwh0emfD_Vzz9EVpPy6EZUjndJku9lnYw2PM5OrBO0"
curl -X GET http://localhost:8000/me/ping \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

**Примеры запросов через gateway (curl)**

```sh
# Логин через gateway
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"P@ssw0rd"}'

# Обновить access по заголовку Authorization
ACCESS_TOKEN="<access_token_from_login>"
curl -i -X POST http://localhost:8000/auth/refresh \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"

# Сменить пароль через gateway
curl -i -X POST http://localhost:8000/auth/change-password \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"P@ssw0rd","newPassword":"N3wP@ss"}'

# Выйти: удаляет refresh
curl -i -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

## Scraper Service

Базовый порт по умолчанию: `8000` (в docker-compose.scraper опубликован на `8002`).

### Здоровье

| Метод | Путь | Описание |
| --- | --- | --- |
| GET | `/health` | Проверка статуса сервиса. |

### Приём результатов скрейпа и форвардинг в scraperCatalog

| Метод | Путь | Тело запроса | Описание | Ответ |
| --- | --- | --- | --- | --- |
| POST | `/scraper/results` | `{ "events": [ { <событие> } ] }` | Принимает пачку событий, отправляет каждое в scraperCatalog `/scraperCatalog/upload`, кладёт `uuid` в Redis для дедупликации. | 202 с `{"sent": <int>, "skipped": <int>, "failed": [ { "uuid": "...", "status_code": int, "detail": "..." } ] }` |
| POST | `/scraper/run` | — | Запускает встроенную логику сбора (функция `run_scrape` в `app/core/collector.py`), затем форвардит результаты как `/scraper/results`. | 202 с той же структурой ответа, что и `/scraper/results`. |
| background | — | — | Периодический автозапуск `run_scrape` + форвардинг каждые `SCRAPE_INTERVAL_SECONDS` (env, по умолчанию 600 сек). | Логи в сервисе; ручек нет. |

**Полный пример запроса (curl)**

```sh
curl -X POST http://localhost:8002/scraper/results \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "uuid": "11111111-1111-1111-1111-111111111111",
        "type": "concert",
        "id": "123",
        "title": "Концерт группы X",
        "description": "Большой сольный концерт",
        "price": 1500,
        "date_prewie": "2024-09-01T18:00:00",
        "date_list": ["2024-09-01T18:00:00", "2024-09-02T19:00:00"],
        "place": "Главная сцена",
        "genre": "rock",
        "age": "18+",
        "image_url": "https://example.com/poster.jpg",
        "url": "https://example.com/event/1"
      }
    ]
  }'
```

**Описание полей события (алиасы поддерживаются)**:
- `uuid` (UUID) — обязателен.
- `type` (str) — обязателен: `concert`, `stand_up` или `standup` (опечатки не принимаются).
- `id` (str?) — опционально, исходный id из источника (кладётся в `source_id`).
- `title` (str) — обязателен.
- `description` (str?) — опционально.
- `price` (int?) — опционально.
- `date_preview` (datetime?, алиас `date_prewie`) — опционально, ISO 8601.
- `date_list` (list[datetime]?, алиас `date_full`) — опционально, ISO 8601.
- `place` (str?) — опционально.
- `genre` (str?, алиас `janre`) — опционально.
- `age` (str?, алиас `raiting`) — опционально.
- `image_url` (str?) — опционально.
- `url` (str?) — опционально.

## ScraperCatalog Service

Базовый порт по умолчанию: `8000` (в docker-compose.scraper опубликован на `8003`).

### Здоровье

| Метод | Путь | Описание |
| --- | --- | --- |
| GET | `/health` | Проверка статуса сервиса. |

### Приём одного события от скрапера

| Метод | Путь | Тело запроса | Описание | Ответ |
| --- | --- | --- | --- | --- |
| POST | `/scraperCatalog/upload` | `{ "uuid": "...", "type": "concert", ... }` | Принимает одно событие от Scraper, определяет таблицу по `type` (`concert` → `concert_events`, `stand_up`/`standup` → `standup_events`), проверяет дубликаты по `uuid`. | 201 `{"detail": "created", "type": "<normalized>"}` или 409/200 с `already_exists`; 400 при неподдерживаемом типе. |
| GET/HEAD | `/scraperCatalog/photos/{path}` | Отдаёт сохранённые постеры (WEBP), которые скачивает upload-ручка. | 200 с изображением или 404. |

**Тело запроса (ключевые поля)**:
- `uuid` (UUID) — обязателен.
- `type` (str) — обязателен: `concert`, `stand_up` или `standup`.
- `id` (str?) — опционально, сохраняется как `source_id`.
- Остальные поля совпадают с описанием в разделе Scraper (`title`, `description`, `price`, /`date_prewie`, `date_list`/`date_full`, `place`, `genre`, `age`, `image_url`, `url`).

**Пример (curl)**

```sh
curl -X POST http://localhost:8003/scraperCatalog/upload \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "11111111-1111-1111-1111-111111111111",
    "type": "stand_up",
    "id": "456",
    "title": "Stand-up вечер",
    "description": "Шоу лучших комиков",
    "price": 700,
    "date_prewie": "2024-09-03T20:00:00",
    "date_list": ["2024-09-03T20:00:00"],
    "place": "Малая сцена",
    "genre": "comedy",
    "age": "18+",
    "image_url": "https://example.com/poster2.jpg",
    "url": "https://example.com/event/2"
  }'
```

**Статика с постерами**

```sh
curl -I http://localhost:8003/scraperCatalog/photos/11111111-1111-1111-1111-111111111111.webp
```
