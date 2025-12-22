from typing import Dict, List, Union
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
                resp = await client.get(f"/scraperCatalog/events?type={type}")
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

async def fetch_event_from_scrapercatalog_by_id(event_id:int, event_type: str = 'all') -> List[EventRead]:
    try:
        async with httpx.AsyncClient(
            base_url=settings.scraper_catalog_service_url,
            timeout=10.0,
        ) as client:
                if event_type and event_type != "all":
                    resp = await client.get(f"/scraperCatalog/events?id={event_id}&type={event_type}")
                else:
                    resp = await client.get(f"/scraperCatalog/events?id={event_id}")
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


async def fetch_best_events_from_scrapercatalog(
    event_type: str | None = None,
    event_id: int | None = None,
) -> List[EventRead]:
    params: Dict[str, Union[str, int]] = {}
    if event_type is not None:
        params["type"] = event_type
    if event_id is not None:
        params["id"] = event_id

    try:
        async with httpx.AsyncClient(
            base_url=settings.scraper_catalog_service_url,
            timeout=10.0,
        ) as client:
            resp = await client.get("/scraperCatalog/best-events", params=params)
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
