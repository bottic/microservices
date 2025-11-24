import os
from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://auth_user:auth_pass@postgres:5432/db_scraper",
    )
    scraper_catalog_service_url: str = os.getenv("SCRAPER_CATALOG_SERVICE_URL", "http://scrapercatalog:8000")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    processed_uuids_key: str = os.getenv("PROCESSED_UUIDS_KEY", "scraper:processed-uuids")


settings = Settings()
