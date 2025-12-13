from typing import List, Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Path, Query
from app.core.redis import get_cached_events, cache_events, get_cached_event_by_id
from app.core.fetch_events import fetch_events_from_scrapercatalog, fetch_event_from_scrapercatalog_by_id
from app.schemas.event import EventRead

router = APIRouter(prefix="/catalog", tags=["catalog"])

NEAREST_DEFAULT_LIMIT = 20
DEFAULT_TZ = ZoneInfo("Europe/Moscow")

SUPPORTED_TYPES = {
    "concert",
    "stand_up",
    "exhibition",
    "theater",
    "cinema",
    "sport",
    "excursion",
    "show",
    "quest",
    "master_class",
}

def _normalize_dt(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=DEFAULT_TZ)
    return dt.astimezone(DEFAULT_TZ)

def _next_event_datetime(event: EventRead, now: datetime) -> Optional[datetime]:
    candidates = [_normalize_dt(dt) for dt in (event.date_list or [])]
    # всегда учитываем date_preview как запасной вариант
    candidates.append(_normalize_dt(event.date_preview))
    future = [dt for dt in candidates if dt >= now]
    return min(future) if future else None

async def _get_events(scope: str) -> List[EventRead]:
    cached = await get_cached_events(scope=scope)
    if cached is not None and len(cached) > 0:
        return cached

    events = await fetch_events_from_scrapercatalog(type=scope)
    await cache_events(events, scope=scope)

    return events

async def _get_event_by_id(event_id: int, scope: str, ) -> EventRead:
    cached_event = await get_cached_event_by_id(event_id=event_id, scope=scope)
    if cached_event is not None and len(cached_event) > 0:
        return cached_event

    events = await fetch_event_from_scrapercatalog_by_id(event_id=event_id, event_type=scope)

    if events:
        return events[0]

    raise HTTPException(status_code=404, detail="event not found")

async def _get_nearest_events(scope: str, limit: int) -> List[EventRead]:
    events = await _get_events(scope=scope)
    now = datetime.now(DEFAULT_TZ)
    with_next = []
    for e in events:
        dt = _next_event_datetime(e, now)
        if dt:
            with_next.append((dt, e))
    with_next.sort(key=lambda x: x[0])
    return [e for _, e in with_next[:limit]]

@router.get("/events", response_model=List[EventRead])
async def get_events_all(
    event_id: int | None = Query(None, alias="id", description="Event ID"),
    event_type: str | None = Query(None, alias="type", description="Event type")
):
    if event_type is not None:
        t = event_type.lower()
        if t not in SUPPORTED_TYPES:
            raise HTTPException(status_code=404, detail="unsupported event type")
        
        if event_id is not None:
            return [await _get_event_by_id(event_id=event_id, scope=t)]
        
        return await _get_events(scope=t)
    
    if event_id is None:
        return await _get_events(scope='all')
    
    return [await _get_event_by_id(event_id=event_id, scope='all')]

@router.get("/events/nearest", response_model=List[EventRead])
async def get_nearest_events(
    limit: int = Query(NEAREST_DEFAULT_LIMIT, ge=1, le=200),
    event_type: str | None = Query(None, alias="type", description="Event type")
):
    scope = "all"
    if event_type is not None:
        t = event_type.lower()
        if t not in SUPPORTED_TYPES:
            raise HTTPException(status_code=404, detail="unsupported event type")
        scope = t
    return await _get_nearest_events(scope=scope, limit=limit)
