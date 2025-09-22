from datetime import datetime, timedelta, timezone
from typing import Optional
import os
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets

load_dotenv()

# --- Password Hashing Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- JWT Configuration ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

# --- CSRF Configuration ---
CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY")

if not SECRET_KEY or not CSRF_SECRET_KEY:
    raise ValueError("Missing JWT_SECRET_KEY or CSRF_SECRET_KEY in environment!")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_secure_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)

# --- NEW CSRF FUNCTIONS ---
def create_csrf_token(session_id: str) -> str:
    """Creates a signed CSRF token."""
    to_encode = {
        "session_id": session_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES * 2)
    }
    return jwt.encode(to_encode, CSRF_SECRET_KEY, algorithm=ALGORITHM)

def validate_csrf_token(token: str, session_id: str) -> bool:
    """Validates a CSRF token against a session ID."""
    try:
        decoded_token = jwt.decode(token, CSRF_SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token.get("session_id") == session_id
    except JWTError:
        return False