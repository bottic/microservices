from fastapi import FastAPI

from app.routers import scraper

app = FastAPI(
    title="Scraper Catalog Service",
    version="0.1.0",
)


@app.get("/health")
async def healthz():
    return {"status": "ok", "service": "scraperCatalog"}


app.include_router(scraper.router)
