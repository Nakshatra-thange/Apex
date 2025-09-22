# File: apex/backend/app/audit_logger.py

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import uuid

from . import crud, models

async def log_event(
    db: AsyncSession,
    action: str,
    user: Optional[models.User],
    request: Optional[Request] = None,
    details: Optional[Dict[str, Any]] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[uuid.UUID] = None
):
    """
    A centralized function to create an audit log entry.
    """
    user_id = user.id if user else None
    await crud.create_audit_log(
        db=db,
        action=action,
        user_id=user_id,
        request=request,
        details=details,
        resource_type=resource_type,
        resource_id=resource_id
    )