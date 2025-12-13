from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from app.core.redis import get_cached_events, cache_events, get_cached_event_by_id
from app.core.fetch_events import fetch_events_from_scrapercatalog, fetch_event_from_scrapercatalog_by_id
from app.schemas.event import EventRead

router = APIRouter(prefix="/catalog", tags=["catalog"])

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


