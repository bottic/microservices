# app/main.py
from fastapi import FastAPI

from app.routers import auth as auth_router

app = FastAPI(
    title="Auth Service",
    version="0.1.0",
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "auth"}


app.include_router(auth_router.router)
