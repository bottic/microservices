from uuid import UUID

import redis.asyncio as redis
from redis.asyncio.client import Redis

from app.config import settings


def _build_client() -> Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


redis_client: Redis = _build_client()

PROCESSED_SET_KEY = settings.processed_uuids_key


async def was_processed(event_id: UUID) -> bool:
    return bool(await redis_client.sismember(PROCESSED_SET_KEY, str(event_id)))


async def mark_processed(event_id: UUID) -> None:
    await redis_client.sadd(PROCESSED_SET_KEY, str(event_id))


async def close_redis() -> None:
    await redis_client.close()
