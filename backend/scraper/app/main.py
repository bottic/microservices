from fastapi import FastAPI

from app.core.redis import close_redis
from app.routers import results

app = FastAPI(
    title="Scraper Service",
    version="0.1.0",
)


@app.get("/health")
async def healthz():
    return {"status": "ok", "service": "scraper"}


@app.on_event("shutdown")
async def shutdown_event():
    await close_redis()


app.include_router(results.router)
