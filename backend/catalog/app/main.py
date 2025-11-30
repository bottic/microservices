from pathlib import Path

from fastapi import FastAPI


from app.routers import catalog

app = FastAPI(
    title="Catalog Service",
    version="0.1.0",
)



@app.get("/health")
async def healthz():
    return {"status": "ok", "service": "catalog"}


app.include_router(catalog.router)
