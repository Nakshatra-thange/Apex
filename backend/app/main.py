from fastapi import FastAPI
from contextlib import asynccontextmanager
from .caching_middleware import ResponseCacheMiddleware
from . import api_auth, api_admin, api_projects, api_users, api_websockets, api_reviews
from .redis_manager import startup_redis_pool, shutdown_redis_pool
from .websocket_manager import manager as ws_manager # Import the WebSocket manager
from starlette.middleware.gzip import GZipMiddleware
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    # Start the Redis pool for the job queue
    await startup_redis_pool()
    # Start the WebSocket manager's Redis listener
    await ws_manager.startup()
    
    yield # The application is now running
    
    # Clean up on shutdown
    await ws_manager.shutdown()
    await shutdown_redis_pool()

app = FastAPI(
    title="Apex API",
    description="The backend API for the Apex Code Review Assistant.",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(ResponseCacheMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
# Include all the API routers
app.include_router(api_auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(api_admin.router, prefix="/admin", tags=["Admin"])
app.include_router(api_projects.router, prefix="/projects", tags=["Projects"])
app.include_router(api_users.router, prefix="/users", tags=["Users"])
app.include_router(api_reviews.router, prefix="/reviews", tags=["Reviews"])
app.include_router(api_websockets.router, tags=["WebSockets"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Apex API!"}