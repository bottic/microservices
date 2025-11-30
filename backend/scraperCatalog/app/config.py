import os
from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@postgresScraper:5432/dbName",
    )
    scraper_service_url: str = os.getenv("SCRAPER_SERVICE_URL", "http://scraper:8000")
    catalog_service_url: str = os.getenv("CATALOG_SERVICE_URL", "http://catalog:8000")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "your-access-key")
    s3_secret_key: str = os.getenv("S3_SECRET_KEY", "your-secret-key")
    s3_endpoint: str = os.getenv("S3_ENDPOINT", "your-s3-endpoint")
    s3_bucket: str = os.getenv("S3_BUCKET", "your-s3-bucket")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")
    s3_base_url: str = os.getenv("S3_BASE_URL", "")
    s3_acl: str = os.getenv("S3_ACL", "public-read")

settings = Settings()
