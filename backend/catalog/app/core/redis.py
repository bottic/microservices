import redis.asyncio as redis
from redis.asyncio.client import Redis
from redis.exceptions import RedisError


import json

from app.config import settings
from typing import List, Optional
from app.schemas.event import EventRead

from pydantic import ValidationError



def _build_client() -> Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


redis_client: Redis = _build_client()

EVENTS_CACHE_PREFIX = settings.events_cache_prefix

async def get_cached_events(scope: str = 'all') -> Optional[List[EventRead]]:
    try:
        key = EVENTS_CACHE_PREFIX + f":{scope}"
        cached_raw = await redis_client.get(key)
    except RedisError:
        return None

    if not cached_raw:
        return None

    try:
        cached_payload = json.loads(cached_raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(cached_payload, list):
        return None

    try:
        return [EventRead.model_validate(event) for event in cached_payload]
    except ValidationError:
        return None

async def get_cached_event_by_id(event_id: int, scope: str = 'all') -> Optional[EventRead]:
    events = await get_cached_events(scope=scope)
    if not events:
        return None

    for event in events:
        if event.id == event_id:
            return event
    return None

async def cache_events(events: List[EventRead], scope: str = "all") -> None:
    try:
        key = EVENTS_CACHE_PREFIX + f":{scope}"
        payload = json.dumps([event.model_dump(mode="json") for event in events])
        await redis_client.set(key, payload, ex=settings.redis_ttl_seconds)
    except RedisError:
        return

async def close_redis() -> None:
    await redis_client.close()

