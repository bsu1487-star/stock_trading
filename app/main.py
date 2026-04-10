from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.monitoring.logger import setup_logging
from app.storage.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="키움 자동매매 시스템",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
