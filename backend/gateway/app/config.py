import os
from pydantic import BaseModel


class Settings(BaseModel):
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://auth:8000")
    catalog_service_url: str = os.getenv("CATALOG_SERVICE_URL", "http://catalog:8000")
    scraper_catalog_service_url: str = os.getenv(
        "SCRAPER_CATALOG_SERVICE_URL",
        "http://scrapercatalog:8000",
    )

    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")

    # новое:
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")  # строка с origin-ами через запятую или "*"


settings = Settings()
