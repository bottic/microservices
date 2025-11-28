# Перед началом работы создайте фалый:

- auth-config.yaml
- gateway-config.yaml
- postgres-secret.yaml

## auth-config.yaml

Пример заполнения

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: auth-config
  namespace: microservices
data:
  DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/dbName
  JWT_SECRET: dev-secret
  JWT_ALGORITHM: HS256
  ACCESS_TOKEN_EXPIRES: "15"
  REFRESH_TOKEN_EXPIRES_DAYS: "30"
```

## gateway-config.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gateway-config
  namespace: microservices
data:
  AUTH_SERVICE_URL: http://auth:8000
  CATALOG_SERVICE_URL: http://catalog:8000
  JWT_SECRET: dev-secret
  JWT_ALGORITHM: HS256
  # CORS_ORIGINS: http://localhost:5173
  CORS_ORIGINS: http://localhost
```

## postgres-secret.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: microservices
type: Opaque
stringData:
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres
  POSTGRES_DB: dbName

```

# Заполните файлы

- auth/.env
- gateway/.env

# Старт

## Первый запуск

```bash {"terminalRows":"16"}
sudo usermod -aG docker $USER && newgrp docker

```

```bash
RESET_MINIKUBE=true IMG_TAG=v1 bash restart.sh
```

После выполнения файла запускаем

```bash
kubectl port-forward svc/gateway 8000:8000 -n microservices --address 0.0.0.0
```

Посмотреть постгрес

```bash
kubectl port-forward -n microservices pod/postgres-0 5433:5432

```

# Локальное тестирование scraper + scraperCatalog (docker-compose)

1. Заполните `.env`:
   - `backend/scraper/.env` (должен содержать `DATABASE_URL`, `SCRAPER_CATALOG_SERVICE_URL`, `REDIS_URL`).
   - `backend/scraperCatalog/.env` (должен содержать `DATABASE_URL`).

2. Запуск сервисов с локальной БД и Redis:

```bash
cd backend
docker compose -f docker-compose.scraper.yml up --build
```

Поднимутся: `redis` (6379), `postgres` (5434 -> 5432), `scrapercatalog` (8003), `scraper` (8002).

3. Примените миграции для `scrapercatalog` (если таблицы не созданы):

```bash
docker compose -f docker-compose.scraper.yml run --rm scrapercatalog alembic upgrade head
```

4. Проверка ручек:

- Прямой приём в scraperCatalog:

```bash
curl -X POST http://localhost:8003/scraper/upload \
  -H "Content-Type: application/json" \
  -d '{"uuid":"11111111-1111-1111-1111-111111111111","title":"Test","description":"desc","price":100}'
```

- Полный цикл через scraper (`/scraper/results` отправит в scraperCatalog и запишет uuid в Redis):

```bash
curl -X POST http://localhost:8002/scraper/results \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "uuid": "22222222-2222-2222-2222-222222222222",
        "title": "Concert",
        "description": "desc",
        "price": 500,
        "date_prewie": "2024-09-01T18:00:00",
        "date_list": ["2024-09-02T19:00:00"],
        "place": "Main stage",
        "genre": "rock",
        "age": "18+",
        "image_url": "https://example.com/poster.jpg",
        "url": "https://example.com/event"
      }
    ]
  }'
```

Повторный запрос с тем же `uuid` вернёт `skipped` (дедупликация через Redis).

## Для перезапуска можно использовать restart.sh (нужны sudo права).

```sh {"terminalRows":"16"}
sudo usermod -aG docker $USER && newgrp docker

```

```sh
bash restart.sh
```

После выполнения файла запускаем

```bash
kubectl port-forward svc/gateway 8000:8000 -n microservices --address 0.0.0.0
```

Посмотреть постгрес

```bash
kubectl port-forward -n microservices pod/postgres-0 5433:5432

```

```bash
curl http://localhost:8000/catalog/events

```

```bash
curl -X POST http://localhost:8002/scraper/run

```

```bash
curl -X POST http://localhost:8002/scraper/results \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "uuid": "33333333-3334-3333-3333-333333333333",
        "type": "stand_up",
        "title": "Test concert",
        "description": "desc",
        "price": 500,
        "date_prewie": "2024-12-01T18:00:00",
        "date_list": ["2024-12-02T19:00:00"],
        "place": "Main stage",
        "genre": "rock",
        "age": "18+",
        "image_url": "https://avatars.mds.yandex.net/get-afishanew/29022/4c08d32f65e3ecc99501790ff879d16a/s760x440",
        "url": "https://example.com/event"
      }
    ]
  }'

```