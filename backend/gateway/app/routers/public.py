from fastapi import APIRouter, HTTPException, Request, Response
import httpx

from app.config import settings

router = APIRouter()


@router.get("/health")
async def healthz():
    return {"status": "ok", "service": "gateway"}


@router.get("/catalog/events")
async def list_events():
    """
    Проксируем события из сервиса catalog (который сам ходит в scraperCatalog).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
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

