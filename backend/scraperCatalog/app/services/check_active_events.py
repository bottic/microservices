from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import (
    ActiveEvent,
    CinemaEvent,
    ConcertEvent,
    ExhibitionEvent,
    ExcursionEvent,
    InactiveEvent,
    MasterClassEvent,
    QuestEvent,
    ShowEvent,
    SportEvent,
    StandUpEvent,
    TheaterEvent,
)

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


def _to_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _next_future_date(event, now: datetime) -> datetime | None:
    future_dates = [d for d in (_to_aware(dt) for dt in (event.date_list or [])) if d and d > now]
    return min(future_dates) if future_dates else None


def _as_storage(dt: datetime | None) -> datetime | None:
    return dt.replace(tzinfo=None) if dt and dt.tzinfo else dt


def _last_date(event) -> datetime | None:
    dates = [d for d in (_to_aware(dt) for dt in (event.date_list or [])) if d]
    preview = _to_aware(event.date_preview)
    if preview:
        dates.append(preview)
    return max(dates) if dates else None


async def move_expired_events(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(select(ActiveEvent))
    active_events = result.scalars().all()

    moved = 0
    updated_preview = 0
    for ev in active_events:
        next_date = _next_future_date(ev, now)
        current_preview = _to_aware(ev.date_preview)

        if next_date and (not current_preview or current_preview <= now):
            ev.date_preview = _as_storage(next_date)
            type_model = TYPE_MODEL_MAP.get(ev.event_type)
            if type_model:
                type_event = await db.scalar(select(type_model).where(type_model.uuid == ev.uuid))
                if type_event:
                    type_event.date_preview = _as_storage(next_date)
            updated_preview += 1
            continue

        last_dt = _last_date(ev)
        if last_dt and last_dt <= now:
            db.add(
                InactiveEvent(
                    uuid=ev.uuid,
                    source_id=ev.source_id,
                    title=ev.title,
                    description=ev.description,
                    price=ev.price,
                    date_preview=ev.date_preview,
                    date_list=ev.date_list,
                    place=ev.place,
                    event_type=ev.event_type,
                    genre=ev.genre,
                    age=ev.age,
                    image_url=ev.image_url,
                    url=ev.url,
                )
            )

            type_model = TYPE_MODEL_MAP.get(ev.event_type)
            if type_model:
                await db.execute(delete(type_model).where(type_model.uuid == ev.uuid))

            await db.delete(ev)
            moved += 1

    if moved or updated_preview:
        await db.commit()
    else:
        await db.rollback()
    return moved
