import os
from pydantic import BaseModel


class Settings(BaseModel):
    scraper_catalog_service_url: str = os.getenv("SCRAPER_CATALOG_SERVICE_URL", "http://scrapercatalog:8000")
    redis_url: str = os.getenv("REDIS_URL", "redis://redisCatalog:6379/0")
    processed_uuids_key: str = os.getenv("PROCESSED_UUIDS_KEY", "catalog:processed-uuids")
    events_cache_key: str = os.getenv("EVENTS_CACHE_KEY", "catalog:events-cache")

settings = Settings()
