from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# --- магия, чтобы можно было импортировать app.*
# Добавляем корень сервиса в sys.path
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Теперь можем импортировать настройки и Base
from app.config import settings  # type: ignore
from app.db.base import Base  # type: ignore

# Это объект конфигурации Alembic, обеспечивает доступ к значениям в .ini
config = context.config

# Подставим реальный DATABASE_URL из настроек
config.set_main_option("sqlalchemy.url", settings.database_url)

# Логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для автогенерации
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме (без реального подключения)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Общая функция запуска миграций, используется и в async, и в sync."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # чтобы alembic отслеживал изменения типов колонок
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Запуск миграций в online-режиме с async engine."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online_sync() -> None:
    """Обёртка для вызова async функции из Alembic."""
    asyncio.run(run_migrations_online())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online_sync()
