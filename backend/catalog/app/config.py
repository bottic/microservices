import os
from pydantic import BaseModel


class Settings(BaseModel):
    scraper_catalog_service_url: str = os.getenv("SCRAPER_CATALOG_SERVICE_URL", "http://scrapercatalog:8000")
    redis_url: str = os.getenv("REDIS_URL", "redis://redisCatalog:6379/0")
    events_cache_prefix: str = os.getenv("EVENTS_CACHE_PREFIX", "catalog:events-cache")
    redis_ttl_seconds: int = int(os.getenv("REDIS_TTL_SECONDS", "1800"))

settings = Settings()
