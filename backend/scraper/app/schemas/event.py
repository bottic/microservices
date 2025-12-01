from datetime import datetime
from uuid import UUID
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ScrapedEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    uuid: UUID = Field(alias="uuid")
    source_id: Optional[str] = Field(default=None, alias="id")
    event_type: str = Field(validation_alias=AliasChoices("type", "event_type"))
    title: str
    description: str
    price: int
    date_preview: datetime = Field(
        validation_alias=AliasChoices("date_preview", "date_prewie"),
    )
    date_list: List[datetime] = Field(
        validation_alias=AliasChoices("date_list", "date_full"),
    )
    place: str
    genre: str = Field(
        validation_alias=AliasChoices("genre", "janre"),
    )
    age: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("age", "raiting"),
    )
    image_url: str
    url: str

    def to_catalog_payload(self) -> dict:
        """
        Приводим события к формату, который ожидает scraperCatalog.
        Даты сериализуем вручную, чтобы httpx/json не споткнулись о datetime.
        """
        return {
            "uuid": str(self.uuid),
            "id": self.source_id,
            "type": self.event_type,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "date_preview": self.date_preview.isoformat() if self.date_preview else None,
            "date_list": [d.isoformat() for d in self.date_list] if self.date_list else None,
            "place": self.place,
            "genre": self.genre,
            "age": self.age,
            "image_url": self.image_url,
            "url": self.url,
        }

class ScrapedEventsBatch(BaseModel):
    events: List[ScrapedEvent]