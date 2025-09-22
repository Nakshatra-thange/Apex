# File: apex/backend/app/rate_limiter.py

import time
import redis
import os
from fastapi import Depends, HTTPException, status, Response, Request # <-- ADD Request
from dotenv import load_dotenv
from typing import Optional

from . import models, dependencies, crud # <-- ADD crud
from .user_roles import UserRole
from .rate_limit_config import TIER_LIMITS, ENDPOINT_LIMITS
from .audit_logger import log_event # <-- ADD THIS IMPORT
from .database import get_db # <-- ADD THIS IMPORT
from sqlalchemy.ext.asyncio import AsyncSession # <-- ADD THIS IMPORT


def rate_limit(endpoint_name: Optional[str] = None):
    """
    A dependency factory that creates a rate limiter with logging.
    """

    async def rate_limit_dependency(
        response: Response,
        request: Request, # <-- ADD request
        current_user: models.User = Depends(dependencies.get_current_user),
        db: AsyncSession = Depends(get_db) # <-- ADD db session
    ):
        if current_user.role == UserRole.ADMIN:
            return

        if endpoint_name and endpoint_name in ENDPOINT_LIMITS:
            limits = ENDPOINT_LIMITS[endpoint_name]
            redis_key = f"rate_limit:{current_user.id}:{endpoint_name}"
        else:
            limits = TIER_LIMITS.get(current_user.role, TIER_LIMITS[UserRole.FREE_USER])
            redis_key = f"rate_limit:{current_user.id}:general"

        bucket_size = limits["bucket_size"]
        refill_rate = limits["refill_rate_per_minute"] / 60

        current_time = time.time()
        user_bucket = redis_client.hgetall(redis_key)
        
        if not user_bucket:
            tokens = float(bucket_size - 1)
            last_refilled_at = current_time
        else:
            tokens = float(user_bucket[b'tokens'])
            last_refilled_at = float(user_bucket[b'last_refilled_at'])

        time_delta = current_time - last_refilled_at
        tokens_to_add = time_delta * refill_rate
        tokens = min(tokens + tokens_to_add, bucket_size)
        last_refilled_at = current_time

        if tokens >= 1:
            tokens -= 1
            redis_client.hmset(redis_key, {"tokens": tokens, "last_refilled_at": last_refilled_at})
            response.headers["X-RateLimit-Limit"] = str(bucket_size)
            response.headers["X-RateLimit-Remaining"] = str(int(tokens))
        else:
            # --- MONITORING AND ALERTING LOGIC ---
            # Before we block the user, we log the event.
            await log_event(
                db=db,
                action="RATE_LIMIT_EXCEEDED",
                user=current_user,
                request=request,
                details={
                    "endpoint": endpoint_name or "general",
                    "limit": bucket_size,
                    "refill_rate_per_minute": limits["refill_rate_per_minute"]
                }
            )
            # --- END OF MONITORING ---
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded.",
                headers={"Retry-After": "60"},
            )

    return rate_limit_dependency