from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field

from src.models.project import ProjectMemberRole, ProjectVisibility


class ProjectBase(BaseModel):
    """Base project fields."""
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(default=None, description="Project description")


class ProjectCreate(ProjectBase):
    """Input schema to create a project."""
    visibility: str = Field(default=ProjectVisibility.PRIVATE.value, description="Project visibility")


class ProjectUpdate(BaseModel):
    """Input schema to update a project."""
    name: Optional[str] = Field(default=None, description="Project name")
    description: Optional[str] = Field(default=None, description="Project description")
    visibility: Optional[str] = Field(default=None, description="Project visibility")
    is_archived: Optional[bool] = Field(default=None, description="Archive flag")


class ProjectMemberOut(BaseModel):
    """Output schema for a project member."""
    user_id: int = Field(..., description="User ID")
    role: str = Field(..., description="Member role in the project")


class ProjectOut(ProjectBase):
    """Output schema for a project including metadata."""
    id: int = Field(..., description="Project ID")
    owner_id: int = Field(..., description="Owner user ID")
    visibility: str = Field(..., description="Visibility scope")
    is_archived: bool = Field(..., description="Archive flag")


class ProjectWithMembers(ProjectOut):
    """Output schema for project details including members list."""
    members: List[ProjectMemberOut] = Field(default_factory=list, description="Project members")


class ProjectMemberAdd(BaseModel):
    """Input schema for adding or updating a member in a project."""
    user_id: int = Field(..., description="User ID to add")
    role: str = Field(default=ProjectMemberRole.MEMBER.value, description="Role for the user")
