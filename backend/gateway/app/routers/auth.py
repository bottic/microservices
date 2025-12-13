from fastapi import APIRouter, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
from app.config import settings

from app.deps.auth import TokenPayload

router = APIRouter(prefix="/auth", tags=["auth"])

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


@router.post("/login")
async def login_proxy(
    request: Request,
    data: dict[str, str] = Body(..., example={"email": "a@b.com", "password": "secret"})
    ):

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.auth_service_url}/auth/login",
                json=data,
                headers={"Content-Type": request.headers.get("content-type", "application/json")},
                cookies=request.cookies,
                timeout=5.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(502, detail=f"Auth service unavailable: {e}")

    return build_json_response(resp)

@router.post("/register")
async def register_proxy(
    request: Request,
    data: dict[str, str] = Body(..., example={"email": "a@b.com", "password": "secret"})
    ):

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.auth_service_url}/auth/register",
                json=data,
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

@router.post("/refresh")
async def refresh_proxy(
    request: Request,
    data: dict[str, str] = Body(..., example={"access_token": "a@b.com", "password": "secret"})
    ):

    body = await request.body()

    headers = {
        "Content-Type": request.headers.get(
            "content-type", "application/json"
        )
    }
    auth_header = request.headers.get("authorization")
    if auth_header:
        headers["Authorization"] = auth_header

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.auth_service_url}/auth/refresh",
                content=body,
                headers=headers,
                cookies=request.cookies,
                timeout=5.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(502, detail=f"Auth service unavailable: {e}")

    return build_json_response(resp)

@router.post("/change-password")
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

@router.post("/logout")
async def logout(request: Request):
    """
    Удаление refresh токена (куки) при логауте через access-токен.
    """

    headers = {
        "Content-Type": request.headers.get(
            "content-type", "application/json"
        )
    }
    auth_header = request.headers.get("authorization")
    if auth_header:
        headers["Authorization"] = auth_header

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.auth_service_url}/auth/logout",
                headers=headers,
                cookies=request.cookies,
                timeout=5.0,
            )
        except httpx.RequestError as e:
            raise HTTPException(502, detail=f"Auth service unavailable: {e}")

    return build_json_response(resp)
