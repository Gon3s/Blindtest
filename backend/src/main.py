from fastapi import FastAPI

from src.api.routes.health import router as health_router
from src.api.routes.rooms import router as rooms_router

app = FastAPI(title="Blindtest API")
app.include_router(health_router)
app.include_router(rooms_router)
