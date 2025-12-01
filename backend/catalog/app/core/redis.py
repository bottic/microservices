import redis.asyncio as redis
from redis.asyncio.client import Redis
from redis.exceptions import RedisError

import httpx
import json

from app.config import settings
from typing import List, Optional, Union
from app.schemas.event import EventRead

from pydantic import ValidationError
from fastapi import HTTPException


def _build_client() -> Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


redis_client: Redis = _build_client()

EVENTS_CACHE_KEY = settings.events_cache_key

async def get_cached_events() -> Optional[List[EventRead]]:
    """
    Возвращает события из кэша, если они есть и корректны.
    При ошибках или отсутствии кэша возвращает None.
    """
    try:
        cached_raw = await redis_client.get(EVENTS_CACHE_KEY)
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


async def cache_events(events: List[EventRead]) -> None:
    try:
        payload = json.dumps([event.model_dump(mode="json") for event in events])
        await redis_client.set(EVENTS_CACHE_KEY, payload)
    except RedisError:
        return


async def fetch_events_from_scrapercatalog() -> List[EventRead]:
    try:
        async with httpx.AsyncClient(
            base_url=settings.scraper_catalog_service_url,
            timeout=10.0,
        ) as client:
            resp = await client.get("/scraperCatalog/events")
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"scraperCatalog unavailable: {exc}",
        ) from exc

    try:
        payload: Union[list, dict] = resp.json()
    except ValueError:
        payload = resp.text

    if not resp.is_success:
        detail = payload.get("detail") if isinstance(payload, dict) else payload
        raise HTTPException(status_code=resp.status_code, detail=detail)

    if not isinstance(payload, list):
        raise HTTPException(
            status_code=502,
            detail="Unexpected response from scraperCatalog",
        )

    return [EventRead.model_validate(event) for event in payload]

async def close_redis() -> None:
    await redis_client.close()
