from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.db.base import Base


class EventMixin:

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4)
    source_id = Column(String, nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    date_preview = Column(DateTime, nullable=False)
    date_list = Column(ARRAY(DateTime), nullable=False)
    place = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    age = Column(String, nullable=True)
    image_url = Column(String, nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ActiveEvent(EventMixin, Base):
    __tablename__ = "active_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_active_events_uuid"),
    )

class InactiveEvent(EventMixin, Base):
    __tablename__ = "inactive_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_inactive_events_uuid"),
    )


class BestEvents(EventMixin, Base):
    __tablename__ = "best_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_best_events_uuid"),
    )


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


class ExhibitionEvent(EventMixin, Base):
    __tablename__ = "exhibition_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_exhibition_events_uuid"),
    )


class TheaterEvent(EventMixin, Base):
    __tablename__ = "theater_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_theater_events_uuid"),
    )


class CinemaEvent(EventMixin, Base):
    __tablename__ = "cinema_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_cinema_events_uuid"),
    )


class SportEvent(EventMixin, Base):
    __tablename__ = "sport_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_sport_events_uuid"),
    )


class ExcursionEvent(EventMixin, Base):
    __tablename__ = "excursion_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_excursion_events_uuid"),
    )


class ShowEvent(EventMixin, Base):
    __tablename__ = "show_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_show_events_uuid"),
    )


class QuestEvent(EventMixin, Base):
    __tablename__ = "quest_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_quest_events_uuid"),
    )


class MasterClassEvent(EventMixin, Base):
    __tablename__ = "master_class_events"
    __table_args__ = (
        UniqueConstraint("uuid", name="uq_master_class_events_uuid"),
    )

