import asyncio
import logging

from fastapi import FastAPI
from app.db.session import AsyncSessionLocal
from app.services.check_active_events import move_expired_events
from app.routers import scraper, catalog

app = FastAPI(
    title="Scraper Catalog Service",
    version="0.1.0",
)

@app.get("/health")
async def healthz():
    return {"status": "ok", "service": "scraperCatalog"}

app.include_router(scraper.router)
app.include_router(catalog.router)

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def schedule_expired_cleanup():
    async def worker():
        while True:
            try:
                async with AsyncSessionLocal() as db:
                    await asyncio.sleep(30)
                    await move_expired_events(db)
            except Exception as exc:  # не дать задаче упасть навсегда
                logger.warning("move_expired_events failed: %s", exc)
            await asyncio.sleep(3570) 
    asyncio.create_task(worker())
