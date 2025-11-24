import uuid

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
