from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenRefreshRequest(BaseModel):
    """Refresh token input schema."""
    refresh_token: str = Field(..., description="Refresh token")


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr = Field(..., description="User email")
    full_name: Optional[str] = Field(default=None, description="Full name")
    role: str = Field(default="user", description="User role")


class UserCreate(BaseModel):
    """User signup input schema."""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    full_name: Optional[str] = Field(default=None, description="Full name")


class UserLogin(BaseModel):
    """User login input schema."""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class UserOut(UserBase):
    """User output schema."""
    id: int = Field(..., description="User ID")
