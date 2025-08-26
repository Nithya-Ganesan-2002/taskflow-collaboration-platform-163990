from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project import Project, ProjectMember, ProjectMemberRole
from src.models.user import User


async def _ensure_project_access(db: AsyncSession, project_id: int, user_id: int) -> Project:
    """Ensure the user has access to the project (owner or member) and return the project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project.owner_id == user_id:
        return project

    member_q = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
    )
    if member_q.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of the project")
    return project


# PUBLIC_INTERFACE
async def create_project(db: AsyncSession, owner: User, name: str, description: Optional[str], visibility: str) -> Project:
    """Create a new project and add the owner as OWNER in membership table."""
    project = Project(name=name, description=description, owner_id=owner.id, visibility=visibility)
    db.add(project)
    await db.flush()  # to obtain project.id

    membership = ProjectMember(project_id=project.id, user_id=owner.id, role=ProjectMemberRole.OWNER.value)
    db.add(membership)

    await db.commit()
    await db.refresh(project)
    return project


# PUBLIC_INTERFACE
async def list_projects_for_user(db: AsyncSession, user_id: int) -> List[Project]:
    """List projects where the user is owner or member."""
    result = await db.execute(
        select(Project).where(
            or_(
                Project.owner_id == user_id,
                Project.id.in_(select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)),
            )
        ).order_by(Project.created_at.desc())
    )
    return list(result.scalars().all())


# PUBLIC_INTERFACE
async def get_project_detail(db: AsyncSession, project_id: int, user_id: int) -> Project:
    """Get a project if accessible by user."""
    return await _ensure_project_access(db, project_id, user_id)


# PUBLIC_INTERFACE
async def update_project(db: AsyncSession, project_id: int, user_id: int, updates: dict) -> Project:
    """Update project fields if user is owner or admin in project."""
    project = await _ensure_project_access(db, project_id, user_id)

    # Allow update if owner or admin member
    if project.owner_id != user_id:
        role_q = await db.execute(
            select(ProjectMember.role).where(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            )
        )
        role = role_q.scalar_one_or_none()
        if role not in (ProjectMemberRole.ADMIN.value, ProjectMemberRole.OWNER.value):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient project role")

    for key, value in updates.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)
    return project


# PUBLIC_INTERFACE
async def delete_project(db: AsyncSession, project_id: int, user_id: int) -> None:
    """Delete a project (owner only)."""
    project = await _ensure_project_access(db, project_id, user_id)
    if project.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can delete the project")

    await db.execute(delete(Project).where(Project.id == project_id))
    await db.commit()


# PUBLIC_INTERFACE
async def add_or_update_member(db: AsyncSession, project_id: int, actor_id: int, target_user_id: int, role: str) -> ProjectMember:
    """Add or update a project member; actor must be owner or admin."""
    project = await _ensure_project_access(db, project_id, actor_id)

    # Role check
    if project.owner_id != actor_id:
        role_q = await db.execute(
            select(ProjectMember.role).where(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == actor_id)
            )
        )
        actor_role = role_q.scalar_one_or_none()
        if actor_role not in (ProjectMemberRole.ADMIN.value, ProjectMemberRole.OWNER.value):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient project role")

    # Upsert membership
    existing_q = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == target_user_id)
        )
    )
    existing = existing_q.scalar_one_or_none()
    if existing:
        existing.role = role
        member = existing
    else:
        member = ProjectMember(project_id=project_id, user_id=target_user_id, role=role)
        db.add(member)

    await db.commit()
    return member


# PUBLIC_INTERFACE
async def remove_member(db: AsyncSession, project_id: int, actor_id: int, target_user_id: int) -> None:
    """Remove a project member; actor must be owner or admin."""
    project = await _ensure_project_access(db, project_id, actor_id)

    if project.owner_id == target_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove project owner")

    if project.owner_id != actor_id:
        role_q = await db.execute(
            select(ProjectMember.role).where(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == actor_id)
            )
        )
        actor_role = role_q.scalar_one_or_none()
        if actor_role not in (ProjectMemberRole.ADMIN.value, ProjectMemberRole.OWNER.value):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient project role")

    await db.execute(
        delete(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == target_user_id)
        )
    )
    await db.commit()
