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
    description: Optional[str] = None
    price: Optional[int] = None
    date_preview: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("date_preview", "date_prewie"),
    )
    date_list: Optional[List[datetime]] = Field(
        default=None,
        validation_alias=AliasChoices("date_list", "date_full"),
    )
    place: Optional[str] = None
    genre: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("genre", "janre"),
    )
    age: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("age", "raiting"),
    )
    image_url: Optional[str] = None
    url: Optional[str] = None

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
        return normalized.replace(" ", "_")


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
