from typing import List, Union
from app.config import settings
from fastapi import HTTPException

import httpx
from app.schemas.event import EventRead

async def fetch_events_from_scrapercatalog(type: str = 'all') -> List[EventRead]:
    try:
        async with httpx.AsyncClient(
            base_url=settings.scraper_catalog_service_url,
            timeout=10.0,
        ) as client:
            if type == 'all':
                resp = await client.get("/scraperCatalog/events")
            else:
                resp = await client.get(f"/scraperCatalog/events/{type}")
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

    return [EventRead.model_validate(event) for event in payload]