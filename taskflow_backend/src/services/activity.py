from __future__ import annotations

from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.activity import Activity, ActivityScope, ActivityType
from src.models.project import Project, ProjectMember
from src.models.task import Task
from src.websockets.manager import manager


async def _ensure_project_member(db: AsyncSession, project_id: int, user_id: int) -> Project:
    """Ensure the user is part of the project (owner or member)."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id == user_id:
        return project
    mem = await db.execute(
        select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
    )
    if mem.scalar_one_or_none() is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of the project")
    return project


# PUBLIC_INTERFACE
async def record_activity(
    db: AsyncSession,
    *,
    project_id: int,
    actor_id: int,
    type: str,
    message: str,
    task_id: Optional[int] = None,
) -> Activity:
    """Record an activity event for a project (and optional task) and broadcast to WebSocket listeners."""
    scope = ActivityScope.TASK.value if task_id is not None else ActivityScope.PROJECT.value
    event = Activity(
        project_id=project_id,
        task_id=task_id,
        actor_id=actor_id,
        scope=scope,
        type=type,
        message=message,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    # Broadcast to project room and task room if applicable
    payload = {
        "channel": "activity",
        "project_id": project_id,
        "task_id": task_id,
        "actor_id": actor_id,
        "scope": scope,
        "type": type,
        "message": message,
        "id": event.id,
        "created_at": event.created_at,
    }
    await manager.broadcast_project(project_id, payload)
    if task_id is not None:
        await manager.broadcast_task(task_id, payload)

    return event


# PUBLIC_INTERFACE
async def get_project_activity(db: AsyncSession, project_id: int, user_id: int, limit: int = 50) -> List[Activity]:
    """Get activity feed for a project for authorized user."""
    await _ensure_project_member(db, project_id, user_id)
    result = await db.execute(
        select(Activity)
        .where(Activity.project_id == project_id)
        .order_by(Activity.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# PUBLIC_INTERFACE
async def get_task_activity(db: AsyncSession, project_id: int, task_id: int, user_id: int, limit: int = 50) -> List[Activity]:
    """Get activity feed for a task for authorized user."""
    await _ensure_project_member(db, project_id, user_id)
    # ensure task belongs to project
    t = await db.execute(select(Task).where(and_(Task.id == task_id, Task.project_id == project_id)))
    if t.scalar_one_or_none() is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    result = await db.execute(
        select(Activity)
        .where(and_(Activity.project_id == project_id, Activity.task_id == task_id))
        .order_by(Activity.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# Re-export enum for consumers
ActivityTypeEnum = ActivityType
