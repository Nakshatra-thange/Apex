from fastapi import APIRouter, Depends, HTTPException, status
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud, models, schemas
from .dependencies import get_current_user
from .database import get_db

router = APIRouter()

@router.post("/{review_id}/feedback", response_model=schemas.FeedbackRead, status_code=status.HTTP_201_CREATED)
async def submit_review_feedback(
    review_id: uuid.UUID,
    feedback_in: schemas.FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Allows a user to submit feedback for an AI-generated review.
    """
    # 1. Fetch the review to make sure it exists
    review = await crud.get_review_by_id(db, review_id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")
        
    # Optional: Add authorization to ensure the user can view this review
    # For now, we assume if they have the ID, they can provide feedback.

    # 2. Check if feedback already exists for this review
    if review.feedback:
        raise HTTPException(status_code=400, detail="Feedback has already been submitted for this review.")

    # 3. Create the new feedback entry
    new_feedback = await crud.create_review_feedback(
        db=db, review=review, user=current_user, feedback_in=feedback_in
    )
    return new_feedback