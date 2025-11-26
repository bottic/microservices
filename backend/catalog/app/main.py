from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import catalog

app = FastAPI(
    title="Catalog Service",
    version="0.1.0",
)

# Photos live in a shared volume mounted at /app/photos (see docker-compose).
# Use the service root so StaticFiles can find the mounted directory.
PHOTOS_DIR = Path(__file__).resolve().parent.parent / "photos"
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/photos", StaticFiles(directory=PHOTOS_DIR), name="photos")


@app.get("/health")
async def healthz():
    return {"status": "ok", "service": "catalog"}


app.include_router(catalog.router)
