from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx
from app.config import settings

from app.deps.auth import TokenPayload

# router = APIRouter(prefix="/auth", tags=["auth"])

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

# @router.post("/login")
# async def login_proxy(request: Request):
#     """
#     Проксируем логин на сервис auth.
#     Тело запроса просто пробрасываем как есть.
#     """
#     body = await request.body()

#     async with httpx.AsyncClient() as client:
#         try:
#             resp = await client.post(
#                 f"{settings.auth_service_url}/auth/login",
#                 content=body,
#                 headers={"Content-Type": request.headers.get("content-type", "application/json")},
#                 cookies=request.cookies,
#                 timeout=5.0,
#             )
#         except httpx.RequestError as e:
#             raise HTTPException(502, detail=f"Auth service unavailable: {e}")

#     return build_json_response(resp)
