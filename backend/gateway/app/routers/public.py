from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx

from app.config import settings

router = APIRouter()


@router.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "gateway"}


def build_json_response(resp: httpx.Response, content_override=None) -> JSONResponse:
    content_type = resp.headers.get("content-type", "")
    content = (
        content_override
        if content_override is not None
        else (
            resp.json()
            if content_type.startswith("application/json")
            else {"raw": resp.text}
        )
    )

    headers = {}
    set_cookie = resp.headers.get("set-cookie")
    if set_cookie:
        headers["set-cookie"] = set_cookie

    return JSONResponse(
        status_code=resp.status_code,
        content=content,
        headers=headers or None,
    )


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
                cookies=request.cookies,
                timeout=5.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(502, detail=f"Auth service unavailable: {e}")

    return build_json_response(resp)


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
                cookies=request.cookies,
                timeout=5.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(502, detail=f"Auth service unavailable: {e}")

    if resp.is_success:
        return build_json_response(resp, content_override={"message": "Succes"})

    return build_json_response(resp)


@router.post("/auth/refresh")
async def refresh_proxy(request: Request):
    """
    Прокси для обновления access-токена по refresh в HttpOnly cookie.
    """
    body = await request.body()

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.auth_service_url}/auth/refresh",
                content=body,
                headers={
                    "Content-Type": request.headers.get(
                        "content-type", "application/json"
                    )
                },
                cookies=request.cookies,
                timeout=5.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(502, detail=f"Auth service unavailable: {e}")

    return build_json_response(resp)

@router.post("/auth/change-password")
async def change_password(request: Request):
    """
    Прокси для смены пароля пользователя.
    """
    body = await request.body()

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.auth_service_url}/auth/change-password",
                content=body,
                headers={
                    "Content-Type": request.headers.get(
                        "content-type", "application/json"
                    )
                },
                cookies=request.cookies,
                timeout=5.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(502, detail=f"Auth service unavailable: {e}")

    return build_json_response(resp)

@router.post("/auth/logout")
async def logout(request: Request):
    """
    Удаление refresh токена (куки) при логауте.
    """

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.auth_service_url}/auth/logout",
                headers={
                    "Content-Type": request.headers.get(
                        "content-type", "application/json"
                    )
                },
                cookies=request.cookies,
                timeout=5.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(502, detail=f"Auth service unavailable: {e}")

    return build_json_response(resp)

# @router.get("/catalog/events")
# async def list_events_proxy(request: Request):
#     """
#     Проксируем список событий на сервис catalog.
#     Пробрасываем query-параметры как есть.
#     """
#     # Получаем query-параметры как dict
#     query_params = dict(request.query_params)

#     async with httpx.AsyncClient() as client:
#         try:
#             resp = await client.get(
#                 f"{settings.catalog_service_url}/events",
#                 params=query_params,
#                 timeout=5.0,
#             )
#         except httpx.RequestError as e:
#             raise HTTPException(502, detail=f"Catalog service unavailable: {e}")

#     return JSONResponse(
#         status_code=resp.status_code,
#         content=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"raw": resp.text},
#     )
