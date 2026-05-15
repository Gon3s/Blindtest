from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.health import router as health_router
from src.api.routes.rooms import router as rooms_router
from src.infrastructure.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    yield


app = FastAPI(title="Blindtest API", lifespan=lifespan)
app.include_router(health_router)
app.include_router(rooms_router)
