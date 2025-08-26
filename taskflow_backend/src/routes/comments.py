from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.db.session import get_db
from src.models.user import User
from src.schemas.comment import CommentCreate, CommentOut, CommentUpdate
from src.services.comments import create_comment, delete_comment, list_comments, update_comment

router = APIRouter(prefix="/projects/{project_id}/tasks/{task_id}/comments", tags=["Comments"])


@router.get(
    "",
    summary="List task comments",
    description="List all comments for a given task within a project. User must be a project member.",
    response_model=List[CommentOut],
)
# PUBLIC_INTERFACE
async def list_task_comments(
    project_id: int,
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CommentOut]:
    """List comments for a task in a project."""
    comments = await list_comments(db, project_id, task_id, current_user.id)
    return [
        CommentOut(
            id=c.id,
            project_id=c.project_id,
            task_id=c.task_id,
            author_id=c.author_id,
            body=c.body,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in comments
    ]


@router.post(
    "",
    summary="Create task comment",
    description="Create a new comment on the specified task.",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
# PUBLIC_INTERFACE
async def create_task_comment(
    project_id: int,
    task_id: int,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentOut:
    """Create a comment on a task."""
    c = await create_comment(db, project_id, task_id, current_user.id, payload.body)
    return CommentOut(
        id=c.id,
        project_id=c.project_id,
        task_id=c.task_id,
        author_id=c.author_id,
        body=c.body,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.patch(
    "/{comment_id}",
    summary="Update task comment",
    description="Update an existing comment's text. Only the author can edit.",
    response_model=CommentOut,
)
# PUBLIC_INTERFACE
async def update_task_comment(
    project_id: int,
    task_id: int,
    comment_id: int,
    payload: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentOut:
    """Update a comment body."""
    c = await update_comment(db, project_id, task_id, comment_id, current_user.id, payload.body or "")
    return CommentOut(
        id=c.id,
        project_id=c.project_id,
        task_id=c.task_id,
        author_id=c.author_id,
        body=c.body,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.delete(
    "/{comment_id}",
    summary="Delete task comment",
    description="Delete a comment from the task. Only the author can delete.",
    status_code=status.HTTP_204_NO_CONTENT,
)
# PUBLIC_INTERFACE
async def delete_task_comment(
    project_id: int,
    task_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a comment from a task."""
    await delete_comment(db, project_id, task_id, comment_id, current_user.id)
    return None
