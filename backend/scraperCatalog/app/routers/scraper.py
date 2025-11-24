from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.event import Event
from app.schemas.event import EventCreate

router = APIRouter(prefix="/scraper", tags=["scraper"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_data(data: EventCreate, db: AsyncSession = Depends(get_db)):
    """
    Принимаем одно событие от сервиса scraper и сохраняем в БД.
    """
    existing = await db.get(Event, data.id)
    if existing:
        return {"detail": "already_exists"}

    event = Event(
        id=data.id,
        title=data.title,
        description=data.description,
        price=data.price,
        date_preview=data.date_preview,
        date_list=data.date_list,
        place=data.place,
        genre=data.genre,
        age=data.age,
        image_url=data.image_url,
        url=data.url,
    )

    db.add(event)
    await db.commit()

    return {"detail": "created"}
