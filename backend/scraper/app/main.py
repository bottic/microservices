import asyncio
import logging
from typing import Optional

from fastapi import FastAPI

from app.core.redis import close_redis
from app.routers import results
from app.config import settings
from app.core.collector import run_scrape
from app.services.forwarder import forward_events_to_catalog
from app.services.init_redis import warmup_processed_from_catalog

app = FastAPI(
    title="Scraper Service",
    version="0.1.0",
)

# Фоновая задача для периодического запуска сборщика.
_scrape_task: Optional[asyncio.Task] = None
logger = logging.getLogger(__name__)


@app.get("/health")
async def healthz():
    return {"status": "ok", "service": "scraper"}


async def _scrape_loop():
    interval = max(settings.scrape_interval_seconds, 5)
    while True:
        try:
            events = await run_scrape()
            if events:
                await forward_events_to_catalog(events)
        except Exception:  # noqa: BLE001
            logger.exception("Periodic scrape failed")

        await asyncio.sleep(interval)


@app.on_event("startup")
async def startup_event():
    global _scrape_task
    await warmup_processed_from_catalog()
    if _scrape_task is None:
        _scrape_task = asyncio.create_task(_scrape_loop())


@app.on_event("shutdown")
async def shutdown_event():
    global _scrape_task  # noqa: PLW0603
    if _scrape_task:
        _scrape_task.cancel()
        try:
            await _scrape_task
        except asyncio.CancelledError:
            pass
        _scrape_task = None

    await close_redis()


app.include_router(results.router)
