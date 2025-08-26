from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    """Base task fields."""
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    status: str = Field(default=TaskStatus.TODO.value, description="Task status")
    priority: str = Field(default=TaskPriority.MEDIUM.value, description="Task priority")
    due_date: Optional[datetime] = Field(default=None, description="Due date")


class TaskCreate(TaskBase):
    """Input schema for creating a task."""
    assignee_id: Optional[int] = Field(default=None, description="Assignee user ID")


class TaskUpdate(BaseModel):
    """Input schema for updating a task."""
    title: Optional[str] = Field(default=None, description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    status: Optional[str] = Field(default=None, description="Task status")
    priority: Optional[str] = Field(default=None, description="Task priority")
    due_date: Optional[datetime] = Field(default=None, description="Due date")
    assignee_id: Optional[int] = Field(default=None, description="Assignee user ID")


class TaskOut(TaskBase):
    """Output schema for tasks."""
    id: int = Field(..., description="Task ID")
    project_id: int = Field(..., description="Project ID")
    assignee_id: Optional[int] = Field(default=None, description="Assignee user ID")
    created_by_id: int = Field(..., description="Creator user ID")
    is_archived: bool = Field(..., description="Archive flag")
