from fastapi import FastAPI
from contextlib import asynccontextmanager

from . import api_auth, api_admin, api_projects, api_users, api_websockets
from .redis_manager import startup_redis_pool, shutdown_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Connects to the Redis job queue on startup.
    Disconnects from the Redis job queue on shutdown.
    """
    await startup_redis_pool()
    yield
    await shutdown_redis_pool()

app = FastAPI(
    title="Apex API",
    description="The backend API for the Apex Code Review Assistant.",
    version="0.1.0",
    lifespan=lifespan # Use the new lifespan context manager
)

# Include all the existing and new routers
app.include_router(api_auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(api_admin.router, prefix="/admin", tags=["Admin"])
app.include_router(api_projects.router, prefix="/projects", tags=["Projects"])
app.include_router(api_users.router, prefix="/users", tags=["Users"])
app.include_router(api_websockets.router, tags=["WebSockets"])

@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to the Apex API!"}