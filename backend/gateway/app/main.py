from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import public
from app.routers import me
from app.routers import auth 

app = FastAPI(
    title="Gateway",
    version="0.1.0",
)

# CORS
if settings.cors_origins == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public.router, tags=["public"])
app.include_router(me.router)
app.include_router(auth.router, tags=["auth"])