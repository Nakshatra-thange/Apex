# File: apex/backend/app/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from typing import List
from .user_roles import UserRole
from . import crud, models, security
from .database import get_db

# This tells FastAPI where to look for the token (in the Authorization header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> models.User:
    """
    Dependency to get the current user from a JWT token.
    - Decodes and validates the token.
    - Fetches the user from the database.
    - Raises an error if the token is invalid or the user doesn't exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # We fetch the user from the DB using the ID from the token
    user = await db.get(models.User, user_id)
    if user is None:
        raise credentials_exception
    return user

def require_role(required_roles: List[UserRole]):
    """
    A dependency that checks if the current user has at least one of
    the required roles.
    """
    
    # This is the actual dependency function that will be executed by FastAPI
    def role_checker(current_user: models.User = Depends(get_current_user)) -> models.User:
        """
        Checks the role of the logged-in user.
        """
        # Check if the user's role is in the list of allowed roles
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to access this resource. Requires one of: {[role.value for role in required_roles]}",
            )
        return current_user

    return role_checker

