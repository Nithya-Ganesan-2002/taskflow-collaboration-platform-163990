from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommentBase(BaseModel):
    """Base comment fields."""
    body: str = Field(..., description="Comment text body")


class CommentCreate(CommentBase):
    """Input schema to create a comment."""
    pass


class CommentUpdate(BaseModel):
    """Input schema to update a comment."""
    body: Optional[str] = Field(default=None, description="Updated comment text")


class CommentOut(CommentBase):
    """Output schema for a task comment."""
    id: int = Field(..., description="Comment ID")
    project_id: int = Field(..., description="Project ID")
    task_id: int = Field(..., description="Task ID")
    author_id: int = Field(..., description="Author user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
