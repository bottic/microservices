from datetime import datetime
from uuid import UUID
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    uuid: UUID = Field(alias="uuid")
    source_id: Optional[str] = Field(default=None, alias="id")
    event_type: str = Field(validation_alias=AliasChoices("type", "event_type"))
    title: str
    description: str
    price: int
    date_preview: datetime = Field(
        validation_alias=AliasChoices("date_preview"),
    )
    date_list: List[datetime] = Field(
        validation_alias=AliasChoices("date_list"),
    )
    place: str
    genre: str = Field(
        validation_alias=AliasChoices("genre"),
    )
    age: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("age"),
    )
    image_url: str
    url: str

    def normalized_type(self) -> str:
        """
        Приводим тип к формату stand_up/concert -> stand_up, без учёта регистра.
        """
        normalized = (
            self.event_type.replace("-", " ")
            .replace("_", " ")
            .strip()
            .lower()
        )
        normalized = normalized.replace(" ", "_")

        aliases = {
            "stand_up": "stand_up",
            "theater": "theater",
            "cinema": "cinema",
            "sport": "sport",
            "excursion": "excursion",
            "quest": "quest",
            "master_class": "master_class",
            "show": "show",
            "concert": "concert",
        }

        return aliases.get(normalized, normalized)


class EventCreateBatch(BaseModel):
    events: List[EventCreate]


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: UUID
    source_id: Optional[str] = None
    title: str
    description: str
    price: int
    date_preview: datetime
    date_list: List[datetime]
    place: str
    event_type: str
    genre: str
    age: Optional[str] = None
    image_url: str
    url: str
    created_at: datetime
