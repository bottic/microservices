from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=True)
    date_preview = Column(DateTime, nullable=True)
    date_list = Column(ARRAY(DateTime), nullable=True)
    place = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    age = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
