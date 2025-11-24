from datetime import datetime
from uuid import UUID
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: UUID = Field(alias="uuid")
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
