import asyncio
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from PIL import Image, UnidentifiedImageError

DEFAULT_TIMEOUT = 15.0
TARGET_EXTENSION = ".webp"
PHOTOS_DIR = Path(__file__).resolve().parent.parent / "photos"


class ImageDownloadError(Exception):
    """Raised when we cannot download or save an image."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _save_webp(image_bytes: bytes, save_path: Path) -> None:
    """
    Convert arbitrary image bytes to WEBP and save.
    """
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            mode = "RGBA" if img.mode in ("RGBA", "LA") else "RGB"
            img.convert(mode).save(save_path, format="WEBP")
    except UnidentifiedImageError as exc:
        raise ImageDownloadError("failed to decode image for conversion") from exc
    except OSError as exc:
        raise ImageDownloadError(f"failed to save image: {exc}") from exc


async def download_image(
    image_url: str,
    filename_stem: str,
    photos_dir: Optional[Path] = None,
) -> Path:
    """
    Download image_url, convert to webp and save it under photos_dir/<filename_stem>.webp.
    """
    parsed = urlparse(image_url)
    if parsed.scheme not in {"http", "https"}:
        raise ImageDownloadError("image_url must use http or https scheme", status_code=400)

    target_dir = photos_dir or PHOTOS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
        try:
            response = await client.get(image_url)
        except httpx.HTTPError as exc:
            raise ImageDownloadError(f"failed to download image: {exc}") from exc

        status_code = response.status_code
        content = response.content

    if status_code >= 400:
        raise ImageDownloadError(f"failed to download image: status {status_code}")

    save_path = target_dir / f"{filename_stem}{TARGET_EXTENSION}"
    await asyncio.to_thread(_save_webp, content, save_path)

    return save_path
