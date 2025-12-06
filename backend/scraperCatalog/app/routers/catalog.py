from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.event import EventRead
from app.models.event import (
    ActiveEvent,
    InactiveEvent,
    CinemaEvent,
    ConcertEvent,
    ExhibitionEvent,
    ExcursionEvent,
    MasterClassEvent,
    QuestEvent,
    ShowEvent,
    SportEvent,
    StandUpEvent,
    TheaterEvent,
)

router = APIRouter(prefix="/scraperCatalog", tags=["catalog"])


TYPE_MODEL_MAP = {
    "concert": ConcertEvent,
    "stand_up": StandUpEvent,
    "exhibition": ExhibitionEvent,
    "theater": TheaterEvent,
    "cinema": CinemaEvent,
    "sport": SportEvent,
    "excursion": ExcursionEvent,
    "show": ShowEvent,
    "quest": QuestEvent,
    "master_class": MasterClassEvent,
}

@router.get("/events", response_model=List[EventRead])
async def list_active_events(
    event_id: int | None = Query(None, alias="id", description="Event ID"),
    event_type: str | None = Query(None, alias="type", description="Event type"),
    db: AsyncSession = Depends(get_db),
):
    model = ActiveEvent
    if event_type is not None:
        normalized = event_type.lower()
        model = TYPE_MODEL_MAP.get(normalized)
        if model is None:
            raise HTTPException(status_code=404, detail="unsupported event type")

    query = select(model)
    if event_id is not None:
        query = query.where(model.id == event_id)

    result = await db.execute(query)
    events = result.scalars().all()

    if event_id is not None and not events:
        raise HTTPException(status_code=404, detail="event not found")

    return [EventRead.model_validate(event) for event in events]

@router.get("/inactive-events", response_model=List[EventRead])
async def list_inactive_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InactiveEvent))
    events = result.scalars().all()
    return [EventRead.model_validate(event) for event in events]
