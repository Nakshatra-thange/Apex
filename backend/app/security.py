# File: apex/backend/app/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import secrets
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

# Load environment variables from .env file
load_dotenv()

# --- Password Hashing Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- JWT Configuration ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15 # The short lifespan for access tokens
REFRESH_TOKEN_EXPIRE_DAYS = 30
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable not set!")


def hash_password(password: str) -> str:
    """Hashes a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default to 15 minutes if no delta is provided
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    Creates a new JWT refresh token with a long expiration.
    """
    expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_secure_token(length: int = 32) -> str:
    """
    Generates a cryptographically secure, URL-safe string.
    """
    return secrets.token_urlsafe(length)