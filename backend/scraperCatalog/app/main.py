from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import scraper
from app.routers import catalog

app = FastAPI(
    title="Scraper Catalog Service",
    version="0.1.0",
)


PHOTOS_DIR = Path(__file__).resolve().parent / "photos"


@app.get("/health")
async def healthz():
    return {"status": "ok", "service": "scraperCatalog"}


app.include_router(scraper.router)
app.include_router(catalog.router)

# Отдаём скачанные постеры как статик.
app.mount(
    "/scraperCatalog/photos",
    StaticFiles(directory=PHOTOS_DIR),
    name="photos",
)
