from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.event import (
    CinemaEvent,
    ConcertEvent,
    Event,
    ExhibitionEvent,
    ExcursionEvent,
    MasterClassEvent,
    QuestEvent,
    ShowEvent,
    SportEvent,
    StandUpEvent,
    TheaterEvent,
)
from app.schemas.event import EventCreate
from app.services.image_downloader import ImageDownloadError, download_image

router = APIRouter(prefix="/scraperCatalog", tags=["scraper"])

# Какие типы отправляем в какие таблицы
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


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_data(data: EventCreate, db: AsyncSession = Depends(get_db)):
    """
    Принимаем одно событие от сервиса scraper и сохраняем в БД.
    Сохраняем в таблицу, которая соответствует типу события.
    """
    normalized_type = data.normalized_type()
    model = TYPE_MODEL_MAP.get(normalized_type)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported event type: {data.event_type}",
        )

    existing_common = await db.scalar(select(Event).where(Event.uuid == data.uuid))
    if existing_common:
        return {"detail": "already_exists"}

    existing = await db.scalar(select(model).where(model.uuid == data.uuid))
    if existing:  # редкий случай несогласованности
        return {"detail": "already_exists"}

    stored_image_url = data.image_url
    if data.image_url:
        try:
            await download_image(data.image_url, str(data.uuid))
            stored_image_url = f"/scraperCatalog/photos/{data.uuid}.webp"
        except ImageDownloadError as exc:
            raise HTTPException(
                status_code=getattr(exc, "status_code", status.HTTP_502_BAD_GATEWAY),
                detail=str(exc),
            ) from exc

    common_event = Event(
        uuid=data.uuid,
        source_id=data.source_id,
        title=data.title,
        description=data.description,
        price=data.price,
        date_preview=data.date_preview,
        date_list=data.date_list,
        place=data.place,
        event_type=normalized_type,
        genre=data.genre,
        age=data.age,
        image_url=stored_image_url,
        url=data.url,
    )

    type_event = model(
        uuid=data.uuid,
        source_id=data.source_id,
        title=data.title,
        description=data.description,
        price=data.price,
        date_preview=data.date_preview,
        date_list=data.date_list,
        place=data.place,
        event_type=normalized_type,
        genre=data.genre,
        age=data.age,
        image_url=stored_image_url,
        url=data.url,
    )

    db.add(common_event)
    db.add(type_event)
    await db.commit()

    return {"detail": "created", "type": normalized_type}
