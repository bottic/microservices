import os
from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@postgresScraper:5432/db_scrapercatalog",
    )
    scraper_service_url: str = os.getenv("SCRAPER_SERVICE_URL", "http://scraper:8000")
    catalog_service_url: str = os.getenv("CATALOG_SERVICE_URL", "http://catalog:8000")


settings = Settings()
