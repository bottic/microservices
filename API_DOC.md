# API Overview

Документация по доступным HTTP-ручкам для сервисов монорепозитория.

## Auth Service
Базовый префикс `/auth` (кроме `/health`).

| Метод | Путь | Тело запроса | Описание | Ответ |
| --- | --- | --- | --- | --- |
| GET | `/health` | — | Проверка статуса сервиса. | `{"status":"ok","service":"auth"}` |
| POST | `/auth/register` | `{ "email": "user@example.com", "password": "string" }` | Создание пользователя, проверка уникальности email. | 201 с `{ "id": "UUID", "email": "string" }`; 400 если email уже есть. |
| POST | `/auth/login` | `{ "email": "...", "password": "..." }` | Проверка учетных данных, выдача access. | 200 с `{ "access_token": "<jwt>", "token_type": "bearer" }` + HttpOnly кука `refresh_token` (path `/auth/refresh`, SameSite=Lax); 401 при неверных данных. |
| POST | `/auth/refresh` | — | Обновление access по refresh-куке `refresh_token`; если куки нет, можно передать токен в `Authorization: Bearer ...`. | 200 с новым `access_token` и обновлённой refresh-кукой; 401 если токена нет/невалиден. |
| POST | `/auth/change-password` | `{ "email": "...", "password": "old", "newPassword": "new" }` | Проверяет старый пароль и меняет на новый. | 200 с новым `access_token` и refresh-кукой; 401 при неверных данных. |
| POST | `/auth/logout` | — | Требует `Authorization: Bearer <access_token>`, удаляет refresh-куку. | 200 `{ "detail": "Logged out" }`; 401 при невалидном токене. |

**Пример**

```sh
curl -i -c cookies.txt -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"P@ssw0rd"}'

curl -i -b cookies.txt -X POST http://localhost:8000/auth/refresh
```

## Gateway Service
Проксирует запросы к Auth и Catalog. Не выпускает собственных токенов — пробрасывает тело, заголовки и куки.

**Публичные**

| Метод | Путь | Описание |
| --- | --- | --- |
| GET | `/health` | Статус gateway. |
| GET | `/catalog/events` | Проксирует в Catalog Service `/catalog/events`; при ошибках upstream возвращает код upstream или 502. |
| POST | `/auth/login` | Прокси в Auth `/auth/login`; Set-Cookie передаётся клиенту. |
| POST | `/auth/register` | Прокси в Auth `/auth/register`; при успехе тело ответа заменяется на `{"message": "Succes"}`. |
| POST | `/auth/refresh` | Прокси в Auth `/auth/refresh`; передаёт Authorization (если есть) и куки. |
| POST | `/auth/change-password` | Прокси в Auth `/auth/change-password`. |
| POST | `/auth/logout` | Прокси в Auth `/auth/logout`; передаёт Authorization/куки. |

**Защищённые**

| Метод | Путь | Описание | Ответ |
| --- | --- | --- | --- |
| GET | `/me/ping` | Требует `Authorization: Bearer <jwt>`, валидируется локально (по secret gateway). | `{ "message": "pong", "user_id": "<sub>" }` или 401. |

**Пример**

```sh
curl -X GET http://localhost:8000/me/ping \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

## Catalog Service
Отдаёт события для фронта, кэшируя их в Redis (`catalog:events-cache`). Базовый префикс `/catalog`.

| Метод | Путь | Описание | Ответ |
| --- | --- | --- | --- |
| GET | `/health` | Статус сервиса. | `{"status":"ok","service":"catalog"}` |
| GET | `/catalog/events` | Возвращает список событий. При промахе кэша тянет из ScraperCatalog `/scraperCatalog/events` и кладёт в кэш. | `[Event]` |

`Event`: `id`, `uuid`, `source_id`, `title`, `description`, `price`, `date_preview`, `date_list`, `place`, `event_type`, `genre`, `age`, `image_url`, `url`, `created_at`.

## Scraper Service
Принимает результаты скрейпа и может запускать сборщик. Базовый префикс `/scraper`. Redis (`scraper:processed-uuids`) используется для дедупликации.

| Метод | Путь | Тело | Описание | Ответ |
| --- | --- | --- | --- | --- |
| GET | `/health` | — | Статус сервиса. | `{"status":"ok","service":"scraper"}` |
| POST | `/scraper/results` | `{ "events": [<ScrapedEvent>] }` | Принимает пачку событий, пересылает их батчами (`BATCH_SIZE`, по умолчанию 100) в ScraperCatalog `/scraperCatalog/upload/batch`, помечает uuid в Redis после успешной записи (или если уже существуют). | 202 `{ "sent": int, "skipped": int, "failed": [ { "uuid": "...", "status_code": int, "detail": "..." } ] }`; 503 если Redis недоступен. |
| POST | `/scraper/run` | — | Запускает `run_scrape()` и отправляет результаты так же, как `/scraper/results`. | 202 с той же структурой или 503 при ошибке Redis. |

Фоновая задача на старте вызывает `run_scrape()` и форвардит результаты каждые `SCRAPE_INTERVAL_SECONDS` (не меньше 5 с).

## ScraperCatalog Service
Сохраняет события в БД и отдаёт их. Базовый префикс `/scraperCatalog`.

| Метод | Путь | Тело | Описание | Ответ |
| --- | --- | --- | --- | --- |
| GET | `/health` | — | Статус сервиса. | `{"status":"ok","service":"scraperCatalog"}` |
| POST | `/scraperCatalog/upload/batch` | `{ "events": [<EventCreate>] }` | Батчевое сохранение событий: создаёт записи в общей и типовых таблицах, скачивает картинки для каждого элемента. Поддерживаемые типы те же, что в одиночной ручке. | 201 `{ "created": [ { "uuid": "...", "type": "..." } ], "skipped": [ { "uuid": "...", "type": "...", "reason": "already_exists|unsupported_type|no_image_url" } ], "failed": [ { "uuid": "...", "type": "...", "reason": "image_download_failed", "detail": "..." } ] }` |
| POST | `/scraperCatalog/upload` | `<EventCreate>` | Одиночная запись события; логика такая же, как в батче, для обратной совместимости. | 201 `{ "detail": "created", "type": "<normalized>" }`; `{ "detail": "already_exists" }` если uuid уже есть; 400 при неподдерживаемом типе; 502/400 при ошибке загрузки изображения. |
| GET | `/scraperCatalog/events` | — | Возвращает все события из общей таблицы без пагинации. | `[Event]` с полями, как в Catalog Service. |

**Схема события (`ScrapedEvent`/`EventCreate`)**

- `uuid` (UUID) — обязательно.
- `type` или `event_type` (str) — обязательно; значения см. выше.
- `id` → сохраняется как `source_id` (опционально).
- `title` (str) — обязательно; `description` (str?), `price` (int?) — опционально.
- `date_preview` (datetime?, алиас `date_prewie`), `date_list` (list[datetime]?, алиас `date_full`).
- `place`, `genre` (алиас `janre`), `age` (алиас `raiting`), `image_url`, `url` — опционально.

**Пример запроса**

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
        "date_preview": "2024-09-01T18:00:00",
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
