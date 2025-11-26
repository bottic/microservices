from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.event import Event
from app.schemas.event import EventRead

router = APIRouter(prefix="/scraperCatalog", tags=["catalog"])


@router.get("/events", response_model=List[EventRead])
async def list_events(db: AsyncSession = Depends(get_db)):
    """
    Возвращает все события из общей таблицы events.
    """
    result = await db.execute(select(Event))
    events = result.scalars().all()
    return [EventRead.model_validate(event) for event in events]
