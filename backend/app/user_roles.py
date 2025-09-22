# File: apex/backend/app/user_roles.py

from enum import Enum

class UserRole(str, Enum):
    FREE_USER = "free_user"
    PREMIUM_USER = "premium_user"
    ADMIN = "admin"