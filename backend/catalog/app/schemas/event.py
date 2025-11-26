from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: UUID
    source_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    price: Optional[int] = None
    date_preview: Optional[datetime] = None
    date_list: Optional[List[datetime]] = None
    place: Optional[str] = None
    event_type: str
    genre: Optional[str] = None
    age: Optional[str] = None
    image_url: Optional[str] = None
    url: Optional[str] = None
    created_at: datetime
