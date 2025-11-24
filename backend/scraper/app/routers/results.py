from fastapi import APIRouter, HTTPException, status
from redis.exceptions import RedisError

from app.core.collector import run_scrape
from app.schemas.event import ScrapedEventsBatch
from app.services.forwarder import forward_events_to_catalog

router = APIRouter(prefix="/scraper", tags=["scraper"])


@router.post("/results", status_code=status.HTTP_202_ACCEPTED)
async def accept_results(batch: ScrapedEventsBatch):
    """
    Принимаем пачку собранных событий, отправляем их в scraperCatalog
    и сохраняем uuid в Redis для дедупликации.
    """
    try:
        summary = await forward_events_to_catalog(batch.events)
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis unavailable: {exc}",
        ) from exc

    return summary


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def run_and_forward():
    """
    Запускаем сбор данных из core-логики и сразу отправляем результаты.
    """
    try:
        events = await run_scrape()
        summary = await forward_events_to_catalog(events)
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis unavailable: {exc}",
        ) from exc

    return summary
