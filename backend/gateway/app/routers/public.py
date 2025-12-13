from fastapi import APIRouter, HTTPException, Request, Response, Query
import httpx

from app.config import settings

router = APIRouter()


@router.get("/health")
async def healthz():
    return {"status": "ok", "service": "gateway"}


# @router.get("/catalog/events")
# async def list_active_events(
#     event_id: int | None = Query(None, alias="id", description="Event ID"),
#     event_type: str | None = Query(None, alias="type", description="Event type")
# ):
#     try:
#         async with httpx.AsyncClient(timeout=10.0) as client:
#             if event_type is not None:
#                 if event_id is not None:
#                     resp = await client.get(f"{settings.catalog_service_url}/catalog/events?id={event_id}&type={event_type}")
#                 else:
#                     resp = await client.get(f"{settings.catalog_service_url}/catalog/events?type={event_type}")
#             elif event_id is not None:
#                 resp = await client.get(f"{settings.catalog_service_url}/catalog/events?id={event_id}")
#             else:
#                 resp = await client.get(f"{settings.catalog_service_url}/catalog/events")
#     except httpx.RequestError as exc:
#         raise HTTPException(502, detail=f"catalog unavailable: {exc}") from exc

#     try:
#         payload = resp.json()
#     except ValueError:
#         payload = resp.text

#     if not resp.is_success:
#         detail = payload.get("detail") if isinstance(payload, dict) else payload
#         raise HTTPException(status_code=resp.status_code, detail=detail)

#     return payload

# @router.get("/catalog/events/nearest")
# async def list_nearest_events(
#     event_type: str | None = Query(None, alias="type", description="Event type"),
#     limit: int = Query(20, ge=1, le=200, alias="limit", description="Number of events to return"),
# ):
#     try:
#         async with httpx.AsyncClient(timeout=10.0) as client:
#             resp = await client.get(f"{settings.catalog_service_url}/catalog/events/nearest?type={event_type}&limit={limit}")
#     except httpx.RequestError as exc:
#         raise HTTPException(502, detail=f"catalog unavailable: {exc}") from exc

#     try:
#         payload = resp.json()
#     except ValueError:
#         payload = resp.text

#     if not resp.is_success:
#         detail = payload.get("detail") if isinstance(payload, dict) else payload
#         raise HTTPException(status_code=resp.status_code, detail=detail)

#     return payload