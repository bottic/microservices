from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx

from app.config import settings

router = APIRouter()


@router.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "gateway"}


@router.post("/auth/login")
async def login_proxy(request: Request):
    """
    Проксируем логин на сервис auth.
    Тело запроса просто пробрасываем как есть.
    """
    body = await request.body()

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.auth_service_url}/auth/login",
                content=body,
                headers={"Content-Type": request.headers.get("content-type", "application/json")},
                timeout=5.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(502, detail=f"Auth service unavailable: {e}")

    return JSONResponse(
        status_code=resp.status_code,
        content=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"raw": resp.text},
    )


@router.post("/auth/register")
async def register_proxy(request: Request):
    """
    Прокси для регистрации пользователя.
    Тело запроса пробрасываем как есть в сервис auth.
    """
    body = await request.body()

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.auth_service_url}/auth/register",
                content=body,
                headers={
                    "Content-Type": request.headers.get(
                        "content-type", "application/json"
                    )
                },
                timeout=5.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(502, detail=f"Auth service unavailable: {e}")

    return JSONResponse(
        status_code=resp.status_code,
        content=(
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {"raw": resp.text}
        ),
    )

@router.get("/catalog/events")
async def list_events_proxy(request: Request):
    """
    Проксируем список событий на сервис catalog.
    Пробрасываем query-параметры как есть.
    """
    # Получаем query-параметры как dict
    query_params = dict(request.query_params)

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.catalog_service_url}/events",
                params=query_params,
                timeout=5.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(502, detail=f"Catalog service unavailable: {e}")

    return JSONResponse(
        status_code=resp.status_code,
        content=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"raw": resp.text},
    )
