from fastapi import Depends, HTTPException, status, Header, WebSocket, Query, WebSocketDisconnect, Request
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
import uuid

from . import crud, models, security
from .database import get_db

# This tells FastAPI where to look for the token (in the Authorization header)
# The tokenUrl is the endpoint the API docs will use to get a token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> models.User:
    """
    Dependency to get the current user from a JWT bearer token.
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
        user_id_str: Optional[str] = payload.get("user_id")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    
    user = await db.get(models.User, user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_from_websocket(
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> models.User:
    """
    Dependency to get the current user from a JWT token passed as a
    query parameter in a WebSocket connection.
    """
    if not token:
        raise WebSocketDisconnect(code=1008, reason="Token not provided")

    credentials_exception = WebSocketDisconnect(code=1008, reason="Could not validate credentials")
    
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id_str: Optional[str] = payload.get("user_id")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    
    user = await db.get(models.User, user_id)
    if user is None:
        raise credentials_exception
    return user


async def verify_csrf_token(
    request: Request,
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token"),
    current_user: models.User = Depends(get_current_user)
):
    """
    Dependency to verify the double-submit CSRF token.
    Checks for the token in the 'X-CSRF-Token' header and validates it
    against a session ID derived from the authenticated user.
    """
    if not x_csrf_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing CSRF token in header")

    # We use the user's unique ID as the session identifier for simplicity
    session_id = str(current_user.id)
    
    if not security.validate_csrf_token(x_csrf_token, session_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")

