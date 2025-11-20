from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Импортируем модели, чтобы они «подвесились» на Base.metadata
from app.models import user  # noqa: F401
