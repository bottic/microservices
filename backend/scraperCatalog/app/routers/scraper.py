from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.event import ConcertEvent, StandUpEvent
from app.schemas.event import EventCreate

router = APIRouter(prefix="/scraperCatalog", tags=["scraperCatalog"])

# Какие типы отправляем в какие таблицы
TYPE_MODEL_MAP = {
    "concert": ConcertEvent,
    "stand_up": StandUpEvent,
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

    existing = await db.scalar(select(model).where(model.uuid == data.uuid))
    if existing:
        return {"detail": "already_exists"}

    event = model(
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
        image_url=data.image_url,
        url=data.url,
    )

    db.add(event)
    await db.commit()

    return {"detail": "created", "type": normalized_type}
