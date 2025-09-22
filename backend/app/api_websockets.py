
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, crud
from .dependencies import get_current_user
from .websocket_manager import manager
from .database import get_db

router = APIRouter()


@router.websocket("/ws/review/{review_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
    # Note: For simplicity, we are not checking auth here,
    # but in a real app, you would add a dependency to get the current user
    # and verify they have permission to view this review.
):
    """
    Handles WebSocket connections for a specific code review.
    """
    await manager.connect(websocket, review_id)
    try:
        # Keep the connection alive, listening for messages (though we won't act on them)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        # This block is executed when the client disconnects
        manager.disconnect(websocket, review_id)
        print(f"Client disconnected from review_id: {review_id}")