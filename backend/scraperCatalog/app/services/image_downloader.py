import asyncio
from io import BytesIO
from urllib.parse import urlparse

import aioboto3
import httpx
from PIL import Image, UnidentifiedImageError

from app.config import settings

DEFAULT_TIMEOUT = 15.0


class ImageDownloadError(Exception):
    """Raised when we cannot download or save an image."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _to_webp_bytes(image_bytes: bytes) -> bytes:
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            buf = BytesIO()
            mode = "RGBA" if img.mode in ("RGBA", "LA") else "RGB"
            img.convert(mode).save(buf, format="WEBP")
            return buf.getvalue()
    except UnidentifiedImageError as exc:
        raise ImageDownloadError("failed to decode image for conversion") from exc


def _build_public_url(key: str) -> str:

    if settings.s3_base_url:
        return f"{settings.s3_base_url.rstrip('/')}/{key}"
    return f"{settings.s3_endpoint.rstrip('/')}/{settings.s3_bucket}/{key}"
    


async def _upload_to_s3(key: str, body: bytes) -> str:
    session = aioboto3.Session(
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    )
    async with session.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        region_name=settings.s3_region,
    ) as client:
        extra = {"ContentType": "image/webp"}
        if settings.s3_acl:
            extra["ACL"] = settings.s3_acl
        await client.put_object(Bucket=settings.s3_bucket, Key=key, Body=body, **extra)

    return _build_public_url(key)


async def download_image(image_url: str, filename_stem: str) -> str:
    parsed = urlparse(image_url)
    if parsed.scheme not in {"http", "https"}:
        raise ImageDownloadError("image_url must use http or https scheme", status_code=400)

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
        try:
            resp = await client.get(image_url)
        except httpx.HTTPError as exc:
            raise ImageDownloadError(f"failed to download image: {exc}") from exc
        if resp.status_code >= 400:
            raise ImageDownloadError(f"failed to download image: status {resp.status_code}")
        content = resp.content

    webp_bytes = await asyncio.to_thread(_to_webp_bytes, content)
    key = f"{filename_stem}.webp".lstrip("/")
    return await _upload_to_s3(key, webp_bytes)

