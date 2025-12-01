import os
from pydantic import BaseModel


class Settings(BaseModel):
    scraper_catalog_service_url: str = os.getenv("SCRAPER_CATALOG_SERVICE_URL", "http://scrapercatalog:8000")
    redis_url: str = os.getenv("REDIS_URL", "redis://redisScraper:6379/0")
    processed_uuids_key: str = os.getenv("PROCESSED_UUIDS_KEY", "scraper:processed-uuids")
    scrape_interval_seconds: int = int(os.getenv("SCRAPE_INTERVAL_SECONDS", "600"))
    batch_size: int = int(os.getenv("BATCH_SIZE", "100"))


settings = Settings()
