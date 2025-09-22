from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, crud
from .dependencies import get_current_user_from_websocket
from .websocket_manager import manager
from .database import get_db

router = APIRouter()


@router.websocket("/ws/review/{review_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user_from_websocket)
):
    """
    Handles secure WebSocket connections for a specific code review.
    Now registers the connection for both review-specific and user-specific notifications.
    """
    review = await crud.get_review_by_id(db, review_id=review_id)
    if not review or not review.code_snippet:
        await websocket.close(code=1011, reason="Review not found.")
        return

    project = review.code_snippet.project
    is_member = any(member.user_id == current_user.id for member in project.member_associations)
    
    if not is_member:
        await websocket.close(code=1008, reason="Not authorized")
        return

    # --- THIS IS THE KEY CHANGE ---
    # We now pass the user_id to the connect and disconnect methods.
    await manager.connect(websocket, user_id=current_user.id, review_id=review_id)
    
    # Heartbeat mechanism to keep the connection alive and detect disconnects
    async def pinger():
        while True:
            await asyncio.sleep(15)
            await websocket.send_text("ping")

    async def receiver():
        await websocket.receive_text() # This will block until a message is received or connection closes

    pinger_task = asyncio.create_task(pinger())
    receiver_task = asyncio.create_task(receiver())

    done, pending = await asyncio.wait(
        [pinger_task, receiver_task], return_when=asyncio.FIRST_COMPLETED
    )
    for task in pending:
        task.cancel()
        
    manager.disconnect(websocket, user_id=current_user.id, review_id=review_id)
    # --- END OF KEY CHANGE -