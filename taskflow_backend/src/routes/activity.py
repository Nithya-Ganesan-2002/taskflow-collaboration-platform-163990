from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.db.session import get_db
from src.models.user import User
from src.schemas.activity import ActivityOut
from src.services.activity import get_project_activity, get_task_activity

router = APIRouter(prefix="/projects", tags=["Activity"])


@router.get(
    "/{project_id}/activity",
    summary="Project activity feed",
    description="Retrieve the activity feed for a project the user has access to. Optional ?limit= for limiting results.",
    response_model=List[ActivityOut],
)
# PUBLIC_INTERFACE
async def project_activity_endpoint(
    project_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ActivityOut]:
    """Return activity events for a project in reverse chronological order."""
    events = await get_project_activity(db, project_id, current_user.id, limit)
    return [
        ActivityOut(
            id=e.id,
            project_id=e.project_id,
            task_id=e.task_id,
            actor_id=e.actor_id,
            scope=e.scope,
            type=e.type,
            message=e.message,
            created_at=e.created_at,
        )
        for e in events
    ]


@router.get(
    "/{project_id}/tasks/{task_id}/activity",
    summary="Task activity feed",
    description="Retrieve the activity feed for a specific task within a project. Optional ?limit= to limit results.",
    response_model=List[ActivityOut],
)
# PUBLIC_INTERFACE
async def task_activity_endpoint(
    project_id: int,
    task_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ActivityOut]:
    """Return activity events for a task in reverse chronological order."""
    events = await get_task_activity(db, project_id, task_id, current_user.id, limit)
    return [
        ActivityOut(
            id=e.id,
            project_id=e.project_id,
            task_id=e.task_id,
            actor_id=e.actor_id,
            scope=e.scope,
            type=e.type,
            message=e.message,
            created_at=e.created_at,
        )
        for e in events
    ]
