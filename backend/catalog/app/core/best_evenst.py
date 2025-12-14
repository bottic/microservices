from typing import List


import httpx
from fastapi import HTTPException
from app.config import settings


async def forward_best_events(event_ids: List[int]):
    try:
        async with httpx.AsyncClient(
            base_url=settings.scraper_catalog_service_url,
            timeout=10.0,
        ) as client:
            resp = await client.post(
                "/scraperCatalog/events/post-best",
                json={"event_ids": event_ids},
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"scraperCatalog unavailable: {exc}",
        ) from exc
    
    try:
        payload = resp.json()
    except ValueError:
        payload = resp.text

    if not resp.is_success:
        detail = payload.get("detail") if isinstance(payload, dict) else payload
        raise HTTPException(status_code=resp.status_code, detail=detail)

    return payload