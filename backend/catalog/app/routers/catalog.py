from typing import List, Union

import httpx
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas.event import EventRead

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/events", response_model=List[EventRead])
async def get_events():
    """
    Отдает события для фронта.
    Забираем данные из scrapercatalog и просто проксируем их наружу.
    """
    try:
        async with httpx.AsyncClient(
            base_url=settings.scraper_catalog_service_url,
            timeout=10.0,
        ) as client:
            resp = await client.get("/scraperCatalog/events")
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"scraperCatalog unavailable: {exc}",
        ) from exc

    try:
        payload: Union[list, dict] = resp.json()
    except ValueError:
        payload = resp.text

    if not resp.is_success:
        detail = payload.get("detail") if isinstance(payload, dict) else payload
        raise HTTPException(status_code=resp.status_code, detail=detail)

    if not isinstance(payload, list):
        raise HTTPException(
            status_code=502,
            detail="Unexpected response from scraperCatalog",
        )

    # Валидируем через pydantic, чтобы привести типы дат/UUID.
    return [EventRead.model_validate(event) for event in payload]
