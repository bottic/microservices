from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, exists, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.event import (
    CinemaEvent,
    ConcertEvent,
    ActiveEvent,
    InactiveEvent,
    ExhibitionEvent,
    ExcursionEvent,
    MasterClassEvent,
    QuestEvent,
    ShowEvent,
    SportEvent,
    StandUpEvent,
    TheaterEvent,
)
from app.schemas.event import EventCreate, EventCreateBatch
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

async def process_event(data: EventCreate, db: AsyncSession) -> dict:
    normalized_type = data.normalized_type()
    model = TYPE_MODEL_MAP.get(normalized_type)
    if model is None:
        return {"status": "skipped", "reason": "unsupported_type", "uuid": str(data.uuid), "type": data.event_type}
    
    stmt = select(
        or_(
            select(exists().where(ActiveEvent.uuid == data.uuid)).scalar_subquery(),
            select(exists().where(InactiveEvent.uuid == data.uuid)).scalar_subquery(),
            select(exists().where(model.uuid == data.uuid)).scalar_subquery(),
        )
    )

    already_exists = bool(await db.scalar(stmt))
    existing = await db.scalar(select(model).where(model.uuid == data.uuid))
    if already_exists or existing:
        return {"status": "skipped", "reason": "already_exists", "uuid": str(data.uuid), "type": normalized_type}
    
    stored_image_url = None
    if data.image_url:
        try:
            stored_image_url = await download_image(data.image_url, str(data.uuid))
        except ImageDownloadError as exc:
            return {
                "status": "failed",
                "reason": "image_download_failed",
                "detail": str(exc),
                "uuid": str(data.uuid),
                "type": normalized_type,
            }
        
    if not stored_image_url:
        return {"status": "skipped", "reason": "no_image_url", "uuid": str(data.uuid), "type": normalized_type}
    
    common_event = ActiveEvent(
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
    return {"status": "created", "uuid": str(data.uuid), "type": normalized_type}
    

@router.post("/upload/batch", status_code=status.HTTP_201_CREATED)
async def upload_data_batch(data: EventCreateBatch, db: AsyncSession = Depends(get_db)):
    created_events = []
    skipped_events = []
    failed_events = []

    try:
        for event_data in data.events:
            result = await process_event(event_data, db)
            if result["status"] == "created":
                created_events.append({"uuid": result["uuid"], "type": result["type"]})

            elif result["status"] == "skipped":
                skipped_events.append(
                    {"uuid": result["uuid"], "type": result["type"], "reason": result["reason"]}
                )
            elif result["status"] == "failed":
                failed_events.append(
                    {
                        "uuid": result["uuid"],
                        "type": result["type"],
                        "reason": result["reason"],
                        "detail": result.get("detail"),
                    }
                )
        await db.commit()
    except Exception as exc:  # noqa: BLE001
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="failed to process batch"
        ) from exc

    return {"created": created_events, "skipped": skipped_events, "failed": failed_events}

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_data(data: EventCreate, db: AsyncSession = Depends(get_db)):
    result = await process_event(data, db)
    if result["status"] == "created":
        try:
            await db.commit()
        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="failed to save event"
            ) from exc
        return {"detail": "created", "uuid": result["uuid"], "type": result["type"]}
    elif result["status"] == "skipped":
        return {"detail": "skipped", "reason": result["reason"], "uuid": result["uuid"], "type": result["type"]}
    elif result["status"] == "failed":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"not created, {result['reason']}: {result.get('detail')}",
        )
    