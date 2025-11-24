# API Overview

Документация по доступным HTTP-ручкам для сервисов монорепозитория.

## Auth Service

Базовый префикс: зависит от окружения (по умолчанию сервис разворачивается на своём контейнере), все пути ниже начинаются с `/`.

### Здоровье

| Метод | Путь | Описание |
| --- | --- | --- |
| GET | `/healthz` | Проверка статуса сервиса. |

**Пример запроса (curl)**

```sh
curl -X GET http://192.168.49.2/api/healthz
```

### Регистрация, вход, пароль

| Метод | Путь | Тело запроса | Описание | Ответ |
| --- | --- | --- | --- | --- |
| POST | `/auth/register` | `{ "email": "user@example.com", "password": "string" }` | Создаёт нового пользователя; валидирует уникальность email. | 201 с объектом пользователя `{ "id": "UUID", "email": "string" }`. Ошибка 400 если email уже существует. |
| POST | `/auth/login` | `{ "email": "user@example.com", "password": "string" }` | Проверяет учетные данные, выдаёт access и ставит refresh в HttpOnly cookie. | 200 с `{ "access_token": "<jwt>", "token_type": "bearer" }` и Set-Cookie `refresh_token=<jwt>; HttpOnly`. Ошибка 401 при неверных данных. |
| POST | `/auth/refresh` | (пустое тело) | Обновляет access-токен по refresh из HttpOnly cookie (обязательно). | 200 с `{ "access_token": "<jwt>", "token_type": "bearer" }` и обновлённым Set-Cookie `refresh_token=<jwt>; HttpOnly`. Ошибка 401 при неверном/просроченном токене. |
| POST | `/auth/change-password` | `{ "email": "user@example.com", "password": "old", "newPassword": "new" }` | Проверяет старый пароль и обновляет на новый, выдаёт свежие access+refresh. | 200 с `{ "access_token": "<jwt>", "token_type": "bearer" }` и Set-Cookie `refresh_token=<jwt>; HttpOnly`. Ошибка 401 при неверных данных. |
| POST | `/auth/logout` | (пустое тело) | Удаляет refresh cookie. | 200 `{ "detail": "Logged out" }`. |

**Примеры запросов (curl)**

```sh
# Регистрация
curl -X POST http://192.168.49.2/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@exam1ple.com","password":"P@ssw0rd"}'
```

```sh
# Регистрация
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@exam1pl.com","password":"P@ssw0rd"}'
```

```sh
# 1) логин, сохранить куку
curl -i -c backend/cookies.txt -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@exam1ple.com","password":"P@ssw0rd"}'

# 2) обновление access с сохранённой кукой
curl -i -b backend/cookies.txt -X POST http://localhost:8000/auth/refresh

```

```sh
curl -i -b backend/cookies.txt -c backend/cookies.txt -X POST http://localhost:8000/auth/logout

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
curl -i -b backend/cookies.txt -X POST http://localhost:8000/auth/logout
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
| GET | `/healthz` | Проверка статуса gateway. | — |
| POST | `/auth/login` | Пробрасывает тело запроса в Auth Service `/auth/login`; контент-тип сохраняется. | Auth Service |
| POST | `/auth/refresh` | Пробрасывает тело и cookie в Auth Service `/auth/refresh`; возвращает Set-Cookie. | Auth Service |
| POST | `/auth/register` | Пробрасывает тело запроса в Auth Service `/auth/register`. | Auth Service |
| POST | `/auth/change-password` | Пробрасывает тело и cookie в Auth Service `/auth/change-password`. | Auth Service |
| POST | `/auth/logout` | Пробрасывает cookie в Auth Service `/auth/logout`. | Auth Service |
| GET | `/catalog/events` | Возвращает список событий, перенося все query-параметры как есть. | Catalog Service |

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
# Логин через gateway, сохраним куки
curl -i -c gw_cookies.txt -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"P@ssw0rd"}'

# Обновить access по refresh из куки
curl -i -b gw_cookies.txt -X POST http://localhost:8000/auth/refresh

# Сменить пароль через gateway
curl -i -b gw_cookies.txt -X POST http://localhost:8000/auth/change-password \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"P@ssw0rd","newPassword":"N3wP@ss"}'

# Выйти: удаляет refresh
curl -i -b gw_cookies.txt -X POST http://localhost:8000/auth/logout
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
| POST | `/scraper/results` | `{ "events": [ { <событие> } ] }` | Принимает пачку событий, отправляет каждое в scraperCatalog `/scraper/upload`, кладёт `uuid` в Redis для дедупликации. | 202 с `{"sent": <int>, "skipped": <int>, "failed": [ { "uuid": "...", "status_code": int, "detail": "..." } ] }` |
| POST | `/scraper/run` | — | Запускает встроенную логику сбора (функция `run_scrape` в `app/core/collector.py`), затем форвардит результаты как `/scraper/results`. | 202 с той же структурой ответа, что и `/scraper/results`. |

**Полный пример запроса (curl)**

```sh
curl -X POST http://localhost:8002/scraper/results \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "uuid": "11111111-1111-1111-1111-111111111111",
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

### Приём событий от scraper

| Метод | Путь | Тело запроса | Описание | Ответ |
| --- | --- | --- | --- | --- |
| POST | `/scraper/upload` | `{ "uuid": "UUID", "title": "str", ... }` | Принимает одно событие и сохраняет в БД (если id новое). | 201 с `{ "detail": "created" }` или `{ "detail": "already_exists" }` при повторном uuid. |

**Пример запроса (curl)**

```sh
curl -X POST http://localhost:8003/scraper/upload \
  -H "Content-Type: application/json" \
  -d '{"uuid":"11111111-1111-1111-1111-111111111111","title":"Test","description":"desc","price":100}'
```

**Тело** использует те же поля, что описаны в разделе Scraper (`uuid`, `title`, `description`, `price`, `date_preview`/`date_prewie`, `date_list`/`date_full`, `place`, `genre`/`janre`, `age`/`raiting`, `image_url`, `url`).
