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

```sh
curl -H "Host: app.local" https://192.168.1.8:8000/doc
```

### Регистрация и вход

| Метод | Путь | Тело запроса | Описание | Ответ |
| --- | --- | --- | --- | --- |
| POST | `/auth/register` | `{ "email": "user@example.com", "password": "string" }` | Создаёт нового пользователя; валидирует уникальность email. | 201 с объектом пользователя `{ "id": "UUID", "email": "string" }`. Ошибка 400 если email уже существует. |
| POST | `/auth/login` | `{ "email": "user@example.com", "password": "string" }` | Проверяет учетные данные, выдаёт access и ставит refresh в HttpOnly cookie. | 200 с `{ "access_token": "<jwt>", "token_type": "bearer" }` и Set-Cookie `refresh_token=<jwt>; HttpOnly`. Ошибка 401 при неверных данных. |
| POST | `/auth/refresh` | (пустое тело) | Обновляет access-токен по refresh из HttpOnly cookie (обязательно). | 200 с `{ "access_token": "<jwt>", "token_type": "bearer" }` и обновлённым Set-Cookie `refresh_token=<jwt>; HttpOnly`. Ошибка 401 при неверном/просроченном токене. |

**Примеры запросов (curl)**

```sh
# Регистрация
curl -X POST http://192.168.49.2/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"P@ssw0rd"}'
```

```sh
# 1) логин, сохранить куку
curl -i -c cookies.txt -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"P@ssw0rd"}'

# 2) обновление access с сохранённой кукой
curl -i -b cookies.txt -X POST http://localhost:8000/auth/refresh

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

## Bookings Service
