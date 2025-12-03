from typing import List

from fastapi import APIRouter, HTTPException, Path

from app.core.redis import get_cached_events, cache_events
from app.core.fetch_events import fetch_events_from_scrapercatalog
from app.schemas.event import EventRead

router = APIRouter(prefix="/catalog", tags=["catalog"])

async def _get_events(scope: str, type: str) -> List[EventRead]:
    cached = await get_cached_events(scope=scope)
    if cached is not None:
        return cached

    events = await fetch_events_from_scrapercatalog(type=type)
    await cache_events(events, scope=scope)

    return events


@router.get("/events", response_model=List[EventRead])
async def get_events_all():
    return await _get_events(scope="all", type='all')


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

@router.get("/events/{event_type}", response_model=List[EventRead])
async def get_events_by_type(
    event_type: str = Path(..., description="concert, theater, ..."),
):
    t = event_type.lower()
    if t not in SUPPORTED_TYPES:
        raise HTTPException(status_code=404, detail="unsupported event type")
    return await _get_events(scope=t, type=t)