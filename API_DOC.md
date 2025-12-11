# API Overview

Документация по доступным HTTP-ручкам для сервисов монорепозитория.

## Auth Service
Базовый префикс `/auth` (кроме `/health`).

| Метод | Путь | Тело запроса | Описание | Ответ |
| --- | --- | --- | --- | --- |
| GET | `/health` | — | Проверка статуса сервиса. | `{"status":"ok","service":"auth"}` |
| POST | `/auth/register` | `{ "email": "user@example.com", "password": "string" }` | Создание пользователя, проверка уникальности email. | 201 `{ "id": "UUID", "email": "string" }`; 400 если email уже есть. |
| POST | `/auth/login` | `{ "email": "...", "password": "..." }` | Проверка учетных данных, выдача access. | 200 `{ "access_token": "<jwt>", "token_type": "bearer" }` + HttpOnly кука `refresh_token` (path `/auth/refresh`, SameSite=Lax); 401 при неверных данных. |
| POST | `/auth/refresh` | — | Обновление access по refresh-куке `refresh_token`; если куки нет, можно передать токен в `Authorization: Bearer ...`. | 200 с новым `access_token` и обновлённой refresh-кукой; 401 если токена нет/невалиден. |
| POST | `/auth/change-password` | `{ "email": "...", "password": "old", "newPassword": "new" }` | Проверяет старый пароль и меняет на новый. | 200 `{ "access_token": "<jwt>", "token_type": "bearer" }` + refresh-кука; 401 при неверных данных. |
| POST | `/auth/logout` | — | Требует `Authorization: Bearer <access_token>`, удаляет refresh-куку. | 200 `{ "detail": "Logged out" }`; 401 при невалидном токене. |

- Кука `refresh_token`: HttpOnly, path `/auth/refresh`, SameSite=Lax (Secure=false в dev).

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
| GET | `/catalog/events` | Проксирует в Catalog `/catalog/events` с теми же query `id`/`type`; при ошибках upstream возвращает код upstream или 502. |

**Auth-прокси**

| Метод | Путь | Описание |
| --- | --- | --- |
| POST | `/auth/login` | Прокси в Auth `/auth/login`; Set-Cookie передаётся клиенту. |
| POST | `/auth/register` | Прокси в Auth `/auth/register`; при успехе тело ответа заменяется на `{"message": "Succes"}`. |
| POST | `/auth/refresh` | Прокси в Auth `/auth/refresh`; передаёт Authorization (если есть) и куки. |
| POST | `/auth/change-password` | Прокси в Auth `/auth/change-password`. |
| POST | `/auth/logout` | Прокси в Auth `/auth/logout`; передаёт Authorization/куки. |

**Защищённые**

| Метод | Путь | Описание | Ответ |
| --- | --- | --- | --- |
| GET | `/me/ping` | Требует `Authorization: Bearer <jwt>`, валидируется локально (по secret gateway). | `{ "message": "pong", "user_id": "<sub>" }` или 401. |

## Catalog Service
Отдаёт события для фронта, кэшируя их в Redis (`catalog:events-cache:<scope>`, TTL по умолчанию 1800 с). Базовый префикс `/catalog`.

| Метод | Путь | Описание | Ответ |
| --- | --- | --- | --- |
| GET | `/health` | Статус сервиса. | `{"status":"ok","service":"catalog"}` |
| GET | `/catalog/events` | Query: `type` (опционально, один из `concert`, `stand_up`, `exhibition`, `theater`, `cinema`, `sport`, `excursion`, `show`, `quest`, `master_class`), `id` (опционально). Без параметров отдаёт кэш `all`, при `type` — кэш по типу, при `id` — список из одного события. 404 если тип не поддержан или событие не найдено. При промахе кэша тянет из ScraperCatalog `/scraperCatalog/events` и кладёт в кэш. | `[Event]` |

## Scraper Service
Принимает результаты скрейпа, может запускать сборщик и регулярно гоняет сборку в фоне. Базовый префикс `/scraper`. Redis (`scraper:processed-uuids`) используется для дедупликации; на старте заполняется UUID-ами из каталога.

| Метод | Путь | Тело | Описание | Ответ |
| --- | --- | --- | --- | --- |
| GET | `/health` | — | Статус сервиса. | `{"status":"ok","service":"scraper"}` |
| POST | `/scraper/results` | `{ "events": [<ScrapedEvent>] }` | Принимает пачку событий, бьёт их на батчи (`BATCH_SIZE`, по умолчанию 100), отфильтровывает уже обработанные UUID в Redis и отправляет оставшиеся в ScraperCatalog `/scraperCatalog/upload/batch`. | 202 `{ "sent": int, "skipped": int, "failed": [ { "uuid": "...", "status_code": int, "detail": "..." } | { "uuids": ["..."], "status_code": 502, "detail": "..." } ] }`; `skipped` включает дубль по Redis или `already_exists`; 503 если Redis недоступен. |
| POST | `/scraper/run` | — | Запускает `run_scrape()` и отправляет результаты так же, как `/scraper/results`. | 202 с той же структурой или 503 при ошибке Redis. |

Фоновая задача на старте вызывает `run_scrape()` каждые `SCRAPE_INTERVAL_SECONDS` (не меньше 5 с) и отправляет результаты.

## ScraperCatalog Service
Сохраняет события в БД и отдаёт их. Базовый префикс `/scraperCatalog`.

| Метод | Путь | Тело | Описание | Ответ |
| --- | --- | --- | --- | --- |
| GET | `/health` | — | Статус сервиса. | `{"status":"ok","service":"scraperCatalog"}` |
| POST | `/scraperCatalog/upload/batch` | `{ "events": [<EventCreate>] }` | Батчевое сохранение событий: создаёт записи в общей и типовых таблицах, скачивает картинку для каждого элемента и конвертирует в WebP в S3. Поддерживаемые типы: `concert`, `stand_up`, `exhibition`, `theater`, `cinema`, `sport`, `excursion`, `show`, `quest`, `master_class` (по другим типам — `skipped`). | 201 `{ "created": [ { "uuid": "...", "type": "..." } ], "skipped": [ { "uuid": "...", "type": "...", "reason": "already_exists|unsupported_type|no_image_url" } ], "failed": [ { "uuid": "...", "type": "...", "reason": "image_download_failed", "detail": "..." } ] }`; 500 `{"detail":"failed to process batch"}` при внутренней ошибке. |
| POST | `/scraperCatalog/upload` | `<EventCreate>` | Одиночная запись события; логика такая же, как в батче. | 201 `{ "detail": "created", "uuid": "...", "type": "..." }` или `{ "detail": "skipped", "reason": "already_exists|unsupported_type|no_image_url", "uuid": "...", "type": "..." }`; 502 `{"detail": "not created, image_download_failed: ..."}` при ошибке загрузки/конвертации изображения; 500 при ошибке сохранения. |
| GET | `/scraperCatalog/events` | — | Возвращает активные события. Query: `type` (опционально, как выше), `id` (опционально). 404 если тип не поддержан или id не найден. | `[Event (scraperCatalog)]` |
| GET | `/scraperCatalog/inactive-events` | — | Возвращает архивные события (перемещаются задачей очистки просроченных дат). | `[Event (scraperCatalog)]` |

Фоновая задача раз в час (после прогрева) обновляет `date_preview` до ближайшей будущей даты или переносит прошедшие события в `inactive_events`.

## Схемы данных

**ScrapedEvent** (тело `/scraper/results` и ответ `run_scrape()`):
- `uuid` (UUID) — обязательно.
- `event_type` или `type` (str) — обязательно.
- `id` → `source_id` (str?) — опционально.
- `title` (str), `description` (str), `price` (int), `date_preview` (datetime или алиас `date_prewie`), `date_list` (list[datetime] или алиас `date_full`), `place` (str), `genre` (алиас `janre`) — обязательны.
- `age` (алиас `raiting`) — опционально.
- `image_url`, `url` (str) — обязательны.
- Лишние поля игнорируются; даты сериализуются в ISO при отправке в ScraperCatalog.

**EventCreate** (ручки `/scraperCatalog/upload*`):
- Обязательные: `uuid`, `event_type`/`type`, `title`, `description`, `price`, `date_preview`, `date_list`, `place`, `genre`, `image_url`, `url`.
- Опциональные: `id`→`source_id`, `age`.
- Алиасы: `event_type`/`type` и `id`; `date_prewie`/`date_full`/`janre`/`raiting` не принимаются.
- Поддерживаемые типы после нормализации к snake_case: `concert`, `stand_up`, `exhibition`, `theater`, `cinema`, `sport`, `excursion`, `show`, `quest`, `master_class`. Неподдержанные типы дают `reason: unsupported_type`.
- `image_url` должен быть http/https; ошибка скачивания/конвертации даёт `image_download_failed`.
- Неизвестные поля игнорируются.

**Event**:
- Catalog Service (`/catalog/events`): `id`, `uuid`, `event_type`, `title`, `created_at` обязательны; остальные (`source_id`, `description`, `price`, `date_preview`, `date_list`, `place`, `genre`, `age`, `image_url`, `url`) могут быть `null`.
- ScraperCatalog ответы: `id`, `uuid`, `title`, `description`, `price`, `date_preview`, `date_list`, `place`, `event_type`, `genre`, `image_url`, `url`, `created_at` обязательны; `source_id`, `age` опциональны.

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
