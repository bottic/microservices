from typing import List

from fastapi import APIRouter

from app.core.redis import get_cached_events, cache_events, fetch_events_from_scrapercatalog
from app.schemas.event import EventRead

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/events", response_model=List[EventRead])
async def get_events():
    """
    Отдает события для фронта.
    Сначала пробуем отдать данные из Redis; при отсутствии — забираем из scrapercatalog
    и кладем их в кэш для последующих запросов.
    """
    cached = await get_cached_events()
    if cached is not None:
        return cached

    events = await fetch_events_from_scrapercatalog()
    await cache_events(events)

    return events
