from fastapi import APIRouter, HTTPException, Request, Response, Query, Body
from typing import List
import httpx
from app.config import settings

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/events")
async def list_active_events(
    event_id: int | None = Query(None, alias="id", description="Event ID"),
    event_type: str | None = Query(None, alias="type", description="Event type")
):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if event_type is not None:
                if event_id is not None:
                    resp = await client.get(f"{settings.catalog_service_url}/catalog/events?id={event_id}&type={event_type}")
                else:
                    resp = await client.get(f"{settings.catalog_service_url}/catalog/events?type={event_type}")
            elif event_id is not None:
                resp = await client.get(f"{settings.catalog_service_url}/catalog/events?id={event_id}")
            else:
                resp = await client.get(f"{settings.catalog_service_url}/catalog/events")
    except httpx.RequestError as exc:
        raise HTTPException(502, detail=f"catalog unavailable: {exc}") from exc

    try:
        payload = resp.json()
    except ValueError:
        payload = resp.text

    if not resp.is_success:
        detail = payload.get("detail") if isinstance(payload, dict) else payload
        raise HTTPException(status_code=resp.status_code, detail=detail)

    return payload

@router.get("/events/nearest")
async def list_nearest_events(
    event_type: str | None = Query(None, alias="type", description="Event type"),
    limit: int = Query(20, ge=1, le=200, alias="limit", description="Number of events to return"),
):
    try:
        if event_type is not None:
            event_type = event_type.lower()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{settings.catalog_service_url}/catalog/events/nearest?type={event_type}&limit={limit}")
        else:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{settings.catalog_service_url}/catalog/events/nearest?limit={limit}")
    except httpx.RequestError as exc:
        raise HTTPException(502, detail=f"catalog unavailable: {exc}") from exc

    try:
        payload = resp.json()
    except ValueError:
        payload = resp.text

    if not resp.is_success:
        detail = payload.get("detail") if isinstance(payload, dict) else payload
        raise HTTPException(status_code=resp.status_code, detail=detail)

    return payload


@router.post("/events/post-best")
async def post_best_events(
    event_ids: List[int] = Body(...,embed=True, description="List of Event IDs"),
    password: str = Body(...,embed=True, description="Admin password for authorization"),
):
    try:
        async with httpx.AsyncClient(
            base_url=settings.catalog_service_url,
            timeout=10.0,
        ) as client:
            resp = await client.post(
                "/catalog/events/post-best",
                json={"event_ids": event_ids, "password": password},
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"catalog unavailable: {exc}",
        ) from exc
    
    try:
        payload = resp.json()
    except ValueError:
        payload = resp.text

    if not resp.is_success:
        detail = payload.get("detail") if isinstance(payload, dict) else payload
        raise HTTPException(status_code=resp.status_code, detail=detail)

    return payload