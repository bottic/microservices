from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx

from app.config import settings

router = APIRouter()


@router.get("/health")
async def healthz():
    return {"status": "ok", "service": "gateway"}


# def build_json_response(resp: httpx.Response, content_override=None) -> JSONResponse:
#     content_type = resp.headers.get("content-type", "")
#     content = (
#         content_override
#         if content_override is not None
#         else (
#             resp.json()
#             if content_type.startswith("application/json")
#             else {"raw": resp.text}
#         )
#     )

#     headers = {}
#     set_cookie = resp.headers.get("set-cookie")
#     if set_cookie:
#         headers["set-cookie"] = set_cookie

#     return JSONResponse(
#         status_code=resp.status_code,
#         content=content,
#         headers=headers or None,
#     )


