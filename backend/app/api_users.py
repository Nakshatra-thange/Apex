from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud, models, schemas
from .dependencies import get_current_user
from .database import get_db

router = APIRouter()

@router.get("/me", response_model=schemas.UserRead)
async def get_own_profile(current_user: models.User = Depends(get_current_user)):
    """Get the profile of the currently authenticated user."""
    return current_user

@router.get("/me/preferences", response_model=schemas.UserPreferences)
async def get_own_preferences(current_user: models.User = Depends(get_current_user)):
    """Get the preferences of the currently authenticated user."""
    # Provide default preferences if none are set
    return current_user.preferences or schemas.UserPreferences().dict()

@router.put("/me/preferences", response_model=schemas.UserRead)
async def update_own_preferences(
    preferences_in: schemas.UserPreferences,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update the preferences of the currently authenticated user."""
    updated_user = await crud.update_user_preferences(db, user=current_user, preferences=preferences_in)
    return updated_user

@router.get("/me/stats", response_model=schemas.UserStats)
async def get_own_stats(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage statistics for the currently authenticated user."""
    stats = await crud.get_user_stats(db, user_id=current_user.id)
    return stats

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_own_account(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete the account of the currently authenticated user.
    This action is irreversible and will delete all associated data.
    """
    await crud.delete_user(db, user=current_user)
    return None