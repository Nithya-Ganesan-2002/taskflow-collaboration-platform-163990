from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.db.session import get_db
from src.models.user import User
from src.schemas.task import TaskCreate, TaskOut, TaskUpdate
from src.services.tasks import assign_task, change_status, create_task, delete_task, list_tasks, update_task

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Tasks"])


@router.get(
    "",
    summary="List tasks",
    description="List tasks for a project the current user has access to.",
    response_model=List[TaskOut],
)
# PUBLIC_INTERFACE
async def list_tasks_endpoint(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TaskOut]:
    """List tasks for a project."""
    tasks = await list_tasks(db, project_id, current_user.id)
    return [
        TaskOut(
            id=t.id,
            project_id=t.project_id,
            title=t.title,
            description=t.description,
            status=t.status,
            priority=t.priority,
            due_date=t.due_date,
            assignee_id=t.assignee_id,
            created_by_id=t.created_by_id,
            is_archived=t.is_archived,
        )
        for t in tasks
    ]


@router.post(
    "",
    summary="Create task",
    description="Create a new task in a project.",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
)
# PUBLIC_INTERFACE
async def create_task_endpoint(
    project_id: int,
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    """Create task."""
    t = await create_task(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        status_value=payload.status,
        priority_value=payload.priority,
        due_date=payload.due_date,
        assignee_id=payload.assignee_id,
    )
    return TaskOut(
        id=t.id,
        project_id=t.project_id,
        title=t.title,
        description=t.description,
        status=t.status,
        priority=t.priority,
        due_date=t.due_date,
        assignee_id=t.assignee_id,
        created_by_id=t.created_by_id,
        is_archived=t.is_archived,
    )


@router.patch(
    "/{task_id}",
    summary="Update task",
    description="Update an existing task.",
    response_model=TaskOut,
)
# PUBLIC_INTERFACE
async def update_task_endpoint(
    project_id: int,
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    """Update task."""
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    t = await update_task(db, project_id, task_id, current_user.id, updates)
    return TaskOut(
        id=t.id,
        project_id=t.project_id,
        title=t.title,
        description=t.description,
        status=t.status,
        priority=t.priority,
        due_date=t.due_date,
        assignee_id=t.assignee_id,
        created_by_id=t.created_by_id,
        is_archived=t.is_archived,
    )


@router.post(
    "/{task_id}/status",
    summary="Change task status",
    description="Change the status of a task.",
    response_model=TaskOut,
)
# PUBLIC_INTERFACE
async def change_task_status_endpoint(
    project_id: int,
    task_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    """Change task status. Payload requires {'status': 'todo|in_progress|done|blocked'}"""
    status_value = payload.get("status")
    t = await change_status(db, project_id, task_id, current_user.id, status_value)
    return TaskOut(
        id=t.id,
        project_id=t.project_id,
        title=t.title,
        description=t.description,
        status=t.status,
        priority=t.priority,
        due_date=t.due_date,
        assignee_id=t.assignee_id,
        created_by_id=t.created_by_id,
        is_archived=t.is_archived,
    )


@router.post(
    "/{task_id}/assignee",
    summary="Assign task",
    description="Assign/unassign a task to a project member. Pass {'assignee_id': <user_id|null>}.",
    response_model=TaskOut,
)
# PUBLIC_INTERFACE
async def assign_task_endpoint(
    project_id: int,
    task_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    """Assign or unassign a task to a project member."""
    assignee_id = payload.get("assignee_id", None)
    t = await assign_task(db, project_id, task_id, current_user.id, assignee_id)
    return TaskOut(
        id=t.id,
        project_id=t.project_id,
        title=t.title,
        description=t.description,
        status=t.status,
        priority=t.priority,
        due_date=t.due_date,
        assignee_id=t.assignee_id,
        created_by_id=t.created_by_id,
        is_archived=t.is_archived,
    )


@router.delete(
    "/{task_id}",
    summary="Delete task",
    description="Delete a task from a project.",
    status_code=status.HTTP_204_NO_CONTENT,
)
# PUBLIC_INTERFACE
async def delete_task_endpoint(
    project_id: int,
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete task."""
    await delete_task(db, project_id, task_id, current_user.id)
    return None
