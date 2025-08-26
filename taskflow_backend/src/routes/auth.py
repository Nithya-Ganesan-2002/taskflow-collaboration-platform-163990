from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.security import create_access_token, create_refresh_token, hash_password, verify_password
from src.core.config import get_settings
from src.db.session import get_db
from src.models.user import User, UserRole
from src.schemas.auth import Token, UserCreate, UserLogin, UserOut, TokenRefreshRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    summary="User signup",
    description="Register a new user account with a unique email.",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created"},
        400: {"description": "Email already registered"},
    },
)
# PUBLIC_INTERFACE
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserOut:
    """Create a new user ensuring unique email and return the user data."""
    # Check existing
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    # Create user
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.USER.value,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role)


@router.post(
    "/login",
    summary="User login",
    description="Authenticate a user and return JWT access and refresh tokens.",
    response_model=Token,
    responses={401: {"description": "Invalid credentials"}},
)
# PUBLIC_INTERFACE
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    """Authenticate user and issue tokens."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    settings = get_settings()
    access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token({"sub": str(user.id), "email": user.email}, expires_delta=access_expires)
    refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post(
    "/refresh",
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token.",
    response_model=Token,
    responses={401: {"description": "Invalid refresh token"}},
)
# PUBLIC_INTERFACE
async def refresh_token(data: TokenRefreshRequest) -> Token:
    """Validate refresh token and return a fresh access token (and new refresh token)."""
    from jose import JWTError
    try:
        payload = __import__("src.auth.security", fromlist=["decode_token"]).decode_token(data.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    email = payload.get("email")
    settings = get_settings()
    access_token = create_access_token({"sub": str(user_id), "email": email}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    # Optionally rotate refresh token
    new_refresh_token = create_refresh_token({"sub": str(user_id), "email": email})
    return Token(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer")


@router.get(
    "/me",
    summary="Get current user",
    description="Return the currently authenticated user's profile.",
    response_model=UserOut,
)
# PUBLIC_INTERFACE
async def read_me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Return the authenticated user's information."""
    return UserOut(id=current_user.id, email=current_user.email, full_name=current_user.full_name, role=current_user.role)
