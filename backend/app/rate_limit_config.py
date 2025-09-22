# File: apex/backend/app/rate_limit_config.py

from .user_roles import UserRole

# Default rate limits per user tier
TIER_LIMITS = {
    UserRole.FREE_USER: {
        "bucket_size": 20,
        "refill_rate_per_minute": 10
    },
    UserRole.PREMIUM_USER: {
        "bucket_size": 100,
        "refill_rate_per_minute": 60
    },
}

# --- NEW SECTION ---
# Special, stricter limits for specific endpoints.
# These will override the user's default tier limit.
ENDPOINT_LIMITS = {
    "login": {
        "bucket_size": 10,
        "refill_rate_per_minute": 5
    }
}