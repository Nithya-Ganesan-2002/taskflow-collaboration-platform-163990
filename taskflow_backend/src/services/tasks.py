from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project import ProjectMember, Project
from src.models.task import Task
from src.services.activity import record_activity, ActivityTypeEnum


async def _ensure_project_member(db: AsyncSession, project_id: int, user_id: int) -> Project:
    """Ensure user is owner or member of project and return project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id == user_id:
        return project
    membership = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
    )
    if membership.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of the project")
    return project


# PUBLIC_INTERFACE
async def list_tasks(db: AsyncSession, project_id: int, user_id: int) -> List[Task]:
    """List tasks for a project if user has access."""
    await _ensure_project_member(db, project_id, user_id)
    result = await db.execute(
        select(Task).where(and_(Task.project_id == project_id, Task.is_archived == False)).order_by(Task.created_at.desc())  # noqa: E712
    )
    return list(result.scalars().all())


# PUBLIC_INTERFACE
async def create_task(
    db: AsyncSession,
    project_id: int,
    user_id: int,
    title: str,
    description: Optional[str],
    status_value: str,
    priority_value: str,
    due_date=None,
    assignee_id: Optional[int] = None,
) -> Task:
    """Create a task for a project. User must be member; assignee must be member as well if provided."""
    await _ensure_project_member(db, project_id, user_id)

    if assignee_id is not None:
        # validate assignee membership
        mem = await db.execute(
            select(ProjectMember).where(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == assignee_id)
            )
        )
        if mem.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignee must be a project member")

    task = Task(
        project_id=project_id,
        title=title,
        description=description,
        status=status_value,
        priority=priority_value,
        due_date=due_date,
        assignee_id=assignee_id,
        created_by_id=user_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Record activity
    await record_activity(
        db,
        project_id=project_id,
        actor_id=user_id,
        type=ActivityTypeEnum.TASK_CREATED.value,
        message=f"Task #{task.id} created: {title}",
        task_id=task.id,
    )
    return task


# PUBLIC_INTERFACE
async def update_task(db: AsyncSession, project_id: int, task_id: int, user_id: int, updates: dict) -> Task:
    """Update a task fields if user has access to the project."""
    await _ensure_project_member(db, project_id, user_id)
    result = await db.execute(select(Task).where(and_(Task.id == task_id, Task.project_id == project_id)))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # if updating assignee, ensure membership
    if "assignee_id" in updates and updates["assignee_id"] is not None:
        mem = await db.execute(
            select(ProjectMember).where(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == updates["assignee_id"])
            )
        )
        if mem.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignee must be a project member")

    for k, v in updates.items():
        setattr(task, k, v)
    await db.commit()
    await db.refresh(task)

    # Record generic update
    await record_activity(
        db,
        project_id=project_id,
        actor_id=user_id,
        type=ActivityTypeEnum.TASK_UPDATED.value,
        message=f"Task #{task.id} updated",
        task_id=task.id,
    )
    return task


# PUBLIC_INTERFACE
async def change_status(db: AsyncSession, project_id: int, task_id: int, user_id: int, status_value: str) -> Task:
    """Change the status of a task."""
    task = await update_task(db, project_id, task_id, user_id, {"status": status_value})
    await record_activity(
        db,
        project_id=project_id,
        actor_id=user_id,
        type=ActivityTypeEnum.TASK_STATUS_CHANGED.value,
        message=f"Task #{task.id} status changed to {status_value}",
        task_id=task.id,
    )
    return task


# PUBLIC_INTERFACE
async def assign_task(db: AsyncSession, project_id: int, task_id: int, user_id: int, assignee_id: int | None) -> Task:
    """Assign a task to a member (or unassign with None)."""
    task = await update_task(db, project_id, task_id, user_id, {"assignee_id": assignee_id})
    await record_activity(
        db,
        project_id=project_id,
        actor_id=user_id,
        type=ActivityTypeEnum.TASK_ASSIGNEE_CHANGED.value,
        message=f"Task #{task.id} assignee changed to {assignee_id if assignee_id is not None else 'none'}",
        task_id=task.id,
    )
    return task


# PUBLIC_INTERFACE
async def delete_task(db: AsyncSession, project_id: int, task_id: int, user_id: int) -> None:
    """Delete a task if user has access to the project (soft delete via archive or hard delete)."""
    await _ensure_project_member(db, project_id, user_id)
    await db.execute(delete(Task).where(and_(Task.id == task_id, Task.project_id == project_id)))
    await db.commit()
    await record_activity(
        db,
        project_id=project_id,
        actor_id=user_id,
        type=ActivityTypeEnum.TASK_DELETED.value,
        message=f"Task #{task_id} deleted",
        task_id=task_id,
    )
