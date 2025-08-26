from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.db.session import get_db
from src.models.user import User
from src.schemas.project import (
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    ProjectMemberAdd,
    ProjectMemberOut,
)
from src.services.projects import (
    add_or_update_member,
    create_project,
    delete_project,
    get_project_detail,
    list_projects_for_user,
    remove_member,
)
# from src.models.project import ProjectMember

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get(
    "",
    summary="List my projects",
    description="List all projects where the current user is owner or member.",
    response_model=List[ProjectOut],
)
# PUBLIC_INTERFACE
async def list_my_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ProjectOut]:
    """List projects for the current user (owner or member)."""
    projects = await list_projects_for_user(db, current_user.id)
    return [
        ProjectOut(
            id=p.id,
            name=p.name,
            description=p.description,
            owner_id=p.owner_id,
            visibility=p.visibility,
            is_archived=p.is_archived,
        )
        for p in projects
    ]


@router.post(
    "",
    summary="Create project",
    description="Create a new project owned by the current user.",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
)
# PUBLIC_INTERFACE
async def create_project_endpoint(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectOut:
    """Create a project."""
    p = await create_project(db, current_user, payload.name, payload.description, payload.visibility)
    return ProjectOut(
        id=p.id,
        name=p.name,
        description=p.description,
        owner_id=p.owner_id,
        visibility=p.visibility,
        is_archived=p.is_archived,
    )


@router.get(
    "/{project_id}",
    summary="Get project",
    description="Get a project by ID if accessible to the current user.",
    response_model=ProjectOut,
)
# PUBLIC_INTERFACE
async def get_project_endpoint(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectOut:
    """Get project details."""
    p = await get_project_detail(db, project_id, current_user.id)
    return ProjectOut(
        id=p.id,
        name=p.name,
        description=p.description,
        owner_id=p.owner_id,
        visibility=p.visibility,
        is_archived=p.is_archived,
    )


@router.patch(
    "/{project_id}",
    summary="Update project",
    description="Update fields on a project (owner or admin).",
    response_model=ProjectOut,
)
# PUBLIC_INTERFACE
async def update_project_endpoint(
    project_id: int,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectOut:
    """Update a project."""
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    p = await __import__("src.services.projects", fromlist=["update_project"]).update_project(db, project_id, current_user.id, updates)
    return ProjectOut(
        id=p.id,
        name=p.name,
        description=p.description,
        owner_id=p.owner_id,
        visibility=p.visibility,
        is_archived=p.is_archived,
    )


@router.delete(
    "/{project_id}",
    summary="Delete project",
    description="Delete a project (owner only).",
    status_code=status.HTTP_204_NO_CONTENT,
)
# PUBLIC_INTERFACE
async def delete_project_endpoint(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a project."""
    await delete_project(db, project_id, current_user.id)
    return None


@router.post(
    "/{project_id}/members",
    summary="Add or update project member",
    description="Add a user to the project or update their role (owner/admin only).",
    response_model=ProjectMemberOut,
)
# PUBLIC_INTERFACE
async def add_member_endpoint(
    project_id: int,
    payload: ProjectMemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberOut:
    """Add or update a project member."""
    member = await add_or_update_member(db, project_id, current_user.id, payload.user_id, payload.role)
    return ProjectMemberOut(user_id=member.user_id, role=member.role)


@router.delete(
    "/{project_id}/members/{user_id}",
    summary="Remove project member",
    description="Remove a user from the project (owner/admin only).",
    status_code=status.HTTP_204_NO_CONTENT,
)
# PUBLIC_INTERFACE
async def remove_member_endpoint(
    project_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a project member."""
    await remove_member(db, project_id, current_user.id, user_id)
    return None
