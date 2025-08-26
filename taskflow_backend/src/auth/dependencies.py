from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.auth.security import decode_token
from src.db.session import get_db
from src.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# PUBLIC_INTERFACE
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """FastAPI dependency that validates a JWT access token and returns the User."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except JWTError:
        raise credentials_exc

    token_type = payload.get("type")
    if token_type != "access":
        raise credentials_exc

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exc
    return user


# PUBLIC_INTERFACE
def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    """Ensure current user has admin role."""
    if str(user.role).lower() != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user
