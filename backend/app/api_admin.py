from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid
from . import schemas
from sqlalchemy.ext.asyncio import AsyncSession

# --- CORRECTED IMPORTS ---
from . import models, schemas, crud, permissions
from .database import get_db # The get_db function comes from database.py


router = APIRouter()


@router.get("/dashboard", response_model=dict)
def get_admin_dashboard(
    current_user: models.User = Depends(permissions.is_admin)
):
    """
    An example protected endpoint that only admin users can access.
    """
    return {
        "message": f"Welcome, Admin User {current_user.email}!",
        "dashboard_data": "Here is some top-secret admin data."
    }


@router.get("/users", response_model=List[schemas.UserRead])
async def list_all_users(
    # --- CORRECTED USAGE ---
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(permissions.is_admin)
):
    """
    Lists all users in the system. Only accessible to administrators.
    """
    users = await crud.get_all_users(db)
    return users


@router.put("/users/{user_id}/role", response_model=schemas.UserRead)
async def set_user_role(
    user_id: uuid.UUID,
    role_update: schemas.UserRoleUpdate,
    # --- CORRECTED USAGE ---
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(permissions.is_admin)
):
    """
    Updates the role of a specific user. Only accessible to administrators.
    """
    user_to_update = await crud.get_user_by_id(db, user_id=user_id)
    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    updated_user = await crud.update_user_role(
        db=db, user=user_to_update, new_role=role_update.role
    )
    return updated_user

@router.put("/users/{user_id}/subscription", response_model=schemas.UserRead)
async def set_user_subscription(
    user_id: uuid.UUID,
    subscription_update: schemas.SubscriptionUpdate,
    # --- CORRECTED USAGE ---
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(permissions.is_admin)
):
    """
    Updates the subscription tier of a specific user. Admin only.
    """
    user_to_update = await crud.get_user_by_id(db, user_id=user_id)
    if not user_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    updated_user = await crud.update_user_subscription(
        db=db, user=user_to_update, tier=subscription_update.subscription_tier
    )
    return updated_user

# (imports are at the top of the file)


# ... (other code) ...

@router.post("/broadcast", status_code=status.HTTP_202_ACCEPTED)
async def broadcast_system_message(
    message: schemas.SystemBroadcast,  # <-- IT IS USED RIGHT HERE
    current_user: models.User = Depends(permissions.is_admin)
):
    """
    Broadcasts a message to all currently connected WebSocket clients.
    This is an admin-only action.
    """
    await ws_manager.broadcast_to_all({
        "type": "system_message",
        "level": message.level.value,
        "text": message.text
    })
    return {"status": "Message broadcast scheduled."}