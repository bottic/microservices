from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.db.base import Base


class EventMixin:
    """
    Общие поля для событий. Наследуем в конкретных таблицах по типу события.
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4)
    source_id = Column(String, nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=True)
    date_preview = Column(DateTime, nullable=True)
    date_list = Column(ARRAY(DateTime), nullable=True)
    place = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    genre = Column(String, nullable=True)
    age = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ConcertEvent(EventMixin, Base):
    __tablename__ = "concert_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_concert_events_uuid"),
    )


class StandUpEvent(EventMixin, Base):
    __tablename__ = "standup_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_standup_events_uuid"),
    )
