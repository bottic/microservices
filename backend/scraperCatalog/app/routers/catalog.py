from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
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
async def list_active_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ActiveEvent))
    events = result.scalars().all()
    return [EventRead.model_validate(event) for event in events]

@router.get("/inactive-events", response_model=List[EventRead])
async def list_inactive_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InactiveEvent))
    events = result.scalars().all()
    return [EventRead.model_validate(event) for event in events]

@router.get("/events/{event_type}", response_model=List[EventRead])
async def list_active_events_by_type(
    event_type: str = Path(..., description="Concert/theater/cinema"),
    db: AsyncSession = Depends(get_db),
):
    normalized = event_type.lower()
    model = TYPE_MODEL_MAP.get(normalized)
    if model is None:
        raise HTTPException(status_code=404, detail="unsupported event type")
    result = await db.execute(select(model))
    events = result.scalars().all()
    return [EventRead.model_validate(event) for event in events]