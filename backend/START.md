# Быстрый старт

**Запуск докера**

```sh
sudo docker compose down --volumes
```

```sh
sudo docker compose up --build
```

**Создание и применение миграций**

```sh
Comment="Описание миграции"
sudo docker compose run --rm auth alembic revision --autogenerate -m "${Comment}"
```

```sh
sudo docker compose run --rm auth alembic upgrade head
```

**Старт работы**

```sh
# Проверка здоровья gateway
curl -X GET http://localhost:8000/healthz
```

