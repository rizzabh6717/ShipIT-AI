from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routers import (
    ai,
    auth,
    deliveries,
    drivers,
    parcels,
    routes,
    uploads,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: ensure the pgvector extension exists."""
    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception:
            # Non-PostgreSQL / extension-not-available environments (e.g. tests
            # against a DB without superuser) should not block startup.
            pass
    yield


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="AI-powered logistics platform: FastAPI + PostgreSQL + pgvector + LangChain.",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Bearer-token auth (no cookies), so credentials stay off. Only the
    # configured frontend origin(s) may call this API.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(drivers.router, prefix=settings.api_v1_prefix)
app.include_router(parcels.router, prefix=settings.api_v1_prefix)
app.include_router(routes.router, prefix=settings.api_v1_prefix)
app.include_router(deliveries.router, prefix=settings.api_v1_prefix)
app.include_router(uploads.router, prefix=settings.api_v1_prefix)
app.include_router(ai.router, prefix=settings.api_v1_prefix)

upload_root = Path(settings.upload_dir)
upload_root.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_root), name="uploads")


@app.get("/health", tags=["System"])
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}
