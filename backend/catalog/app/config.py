import os
from pydantic import BaseModel


class Settings(BaseModel):
    scraper_catalog_service_url: str = os.getenv("SCRAPER_CATALOG_SERVICE_URL", "http://scrapercatalog:8000")



settings = Settings()
