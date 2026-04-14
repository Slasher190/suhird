import logging
from contextlib import asynccontextmanager
from pathlib import Path

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.config import settings

logger = logging.getLogger("suhird")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    photos_dir = Path(settings.local_storage_path)
    photos_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Suhird bot started on port 8000")
    yield
    # Shutdown
    await app.state.redis.close()
    logger.info("Suhird bot stopped")


app = FastAPI(
    title="Suhird (सुहृद्)",
    description="WhatsApp-based matchmaking platform — a good-hearted friend helping people find love.",
    version="1.0.0",
    lifespan=lifespan,
)

photos_dir = Path(settings.local_storage_path)
photos_dir.mkdir(parents=True, exist_ok=True)
app.mount("/photos", StaticFiles(directory=str(photos_dir)), name="photos")

# Routers are imported after app creation to avoid circular imports
from src.api.users import router as users_router  # noqa: E402
from src.api.matches import router as matches_router  # noqa: E402
from src.api.webhook import router as webhook_router  # noqa: E402

app.include_router(users_router)
app.include_router(matches_router)
app.include_router(webhook_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "suhird"}
