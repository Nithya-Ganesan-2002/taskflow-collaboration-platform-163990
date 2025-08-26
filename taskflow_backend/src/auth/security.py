from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt
from passlib.context import CryptContext

from src.core.config import get_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# PUBLIC_INTERFACE
def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token with optional expiration."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


# PUBLIC_INTERFACE
def create_refresh_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT refresh token with optional expiration."""
    settings = get_settings()
    # Default refresh expiration longer than access token
    refresh_minutes = settings.REFRESH_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(minutes=refresh_minutes)
    )
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


# PUBLIC_INTERFACE
def decode_token(token: str) -> dict[str, Any]:
    """Decode a JWT token and return payload if valid, else raise JWTError."""
    settings = get_settings()
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    return payload
