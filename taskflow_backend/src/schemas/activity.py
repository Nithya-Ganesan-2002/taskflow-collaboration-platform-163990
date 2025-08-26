from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ActivityOut(BaseModel):
    """Output schema for an activity feed event."""
    id: int = Field(..., description="Activity ID")
    project_id: int = Field(..., description="Project ID")
    task_id: Optional[int] = Field(default=None, description="Task ID if applicable")
    actor_id: int = Field(..., description="Actor user ID")
    scope: str = Field(..., description="Scope of the event: project|task")
    type: str = Field(..., description="Event type")
    message: str = Field(..., description="Human-readable message")
    created_at: datetime = Field(..., description="Timestamp of the event")
