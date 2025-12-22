from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
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
    BestEvents
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

@router.post("/events/post-best")
async def post_best_events(
    event_ids: List[int] = Body(...,embed=True, description="List of Event IDs"),
    db: AsyncSession = Depends(get_db),
):
    
    if not event_ids:
        raise HTTPException(status_code=400, detail="ids cannot be empty")

    result = await db.execute(select(ActiveEvent).where(ActiveEvent.id.in_(event_ids)))
    events = result.scalars().all()

    if not events:
        raise HTTPException(status_code=404, detail="no events found for the given IDs")

    found_ids = {event.id for event in events}
    not_found_ids = sorted(set(event_ids) - found_ids)

    event_uuids = [event.uuid for event in events]
    existing_best = await db.execute(select(BestEvents.uuid).where(BestEvents.uuid.in_(event_uuids)))
    existing_uuids = set(existing_best.scalars().all())

    added_count = 0
    for event in events:
        if event.uuid in existing_uuids:
            continue
        best_event = BestEvents(
            id = event.id,
            uuid=event.uuid,
            source_id=event.source_id,
            title=event.title,
            description=event.description,
            price=event.price,
            date_preview=event.date_preview,
            date_list=event.date_list,
            place=event.place,
            event_type=event.event_type,
            genre=event.genre,
            age=event.age,
            image_url=event.image_url,
            url=event.url,
        )

        db.add(best_event)

        added_count += 1

    try:
        if added_count:
            await db.commit()
    except Exception as exc:  
        await db.rollback()
        raise HTTPException(status_code=500, detail="failed to save best events") from exc

    return {
        "status": "success",
        "added_event_count": added_count,
        "skipped_existing_uuids": [str(uuid) for uuid in existing_uuids],
        "not_found_ids": not_found_ids,
    }

@router.get("/best-events", response_model=List[EventRead])
async def list_best_events(
    event_type: str | None = Query(None, alias="type", description="Event type"),
    event_id: int | None = Query(None, alias="id", description="Event ID"),
    db: AsyncSession = Depends(get_db)
    ):

    query = select(BestEvents)

    if event_type is not None:
        normalized = event_type.lower()
        if normalized not in TYPE_MODEL_MAP:
            raise HTTPException(status_code=404, detail="unsupported event type")
        
        query = select(BestEvents).where(BestEvents.event_type == normalized)

    if event_id is not None:
        query = query.where(BestEvents.id == event_id)
    
    result = await db.execute(query)
    events = result.scalars().all() 

    if event_id is not None and not events:
        raise HTTPException(status_code=404, detail="event not found")
    
    return [EventRead.model_validate(event) for event in events]