from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.event import ActiveEvent, InactiveEvent
from app.schemas.event import EventRead

router = APIRouter(prefix="/scraperCatalog", tags=["catalog"])


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