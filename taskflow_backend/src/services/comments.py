from __future__ import annotations

from typing import List

from fastapi import HTTPException, status
from sqlalchemy import and_, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.comment import Comment
from src.models.project import Project, ProjectMember
from src.models.task import Task
from src.services.activity import record_activity, ActivityTypeEnum
from src.websockets.manager import manager


async def _ensure_member_and_task(db: AsyncSession, project_id: int, task_id: int, user_id: int) -> Task:
    """Ensure the user is member of the project and the task exists under the project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not (project.owner_id == user_id):
        membership = await db.execute(
            select(ProjectMember).where(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            )
        )
        if membership.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of the project")
    task_q = await db.execute(select(Task).where(and_(Task.id == task_id, Task.project_id == project_id)))
    task = task_q.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


# PUBLIC_INTERFACE
async def list_comments(db: AsyncSession, project_id: int, task_id: int, user_id: int) -> List[Comment]:
    """List comments for a task within a project if the user has access."""
    await _ensure_member_and_task(db, project_id, task_id, user_id)
    result = await db.execute(
        select(Comment).where(
            and_(Comment.project_id == project_id, Comment.task_id == task_id)
        ).order_by(Comment.created_at.asc())
    )
    return list(result.scalars().all())


# PUBLIC_INTERFACE
async def create_comment(db: AsyncSession, project_id: int, task_id: int, user_id: int, body: str) -> Comment:
    """Create a new comment on a task by an authorized project member."""
    await _ensure_member_and_task(db, project_id, task_id, user_id)
    c = Comment(project_id=project_id, task_id=task_id, author_id=user_id, body=body)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    # Record activity
    await record_activity(
        db,
        project_id=project_id,
        actor_id=user_id,
        type=ActivityTypeEnum.COMMENT_ADDED.value,
        message=f"Comment added to task #{task_id}",
        task_id=task_id,
    )
    await manager.broadcast_project(project_id, {
        "channel": "comment",
        "event": "created",
        "project_id": project_id,
        "task_id": task_id,
        "comment": {
            "id": c.id,
            "author_id": c.author_id,
            "body": c.body,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
    })
    await manager.broadcast_task(task_id, {
        "channel": "comment",
        "event": "created",
        "task_id": task_id,
        "comment_id": c.id,
    })
    return c


# PUBLIC_INTERFACE
async def update_comment(db: AsyncSession, project_id: int, task_id: int, comment_id: int, user_id: int, body: str) -> Comment:
    """Update a comment body. Only the author can edit."""
    await _ensure_member_and_task(db, project_id, task_id, user_id)
    result = await db.execute(
        select(Comment).where(
            and_(
                Comment.id == comment_id,
                Comment.project_id == project_id,
                Comment.task_id == task_id,
            )
        )
    )
    comment = result.scalar_one_or_none()
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.author_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can edit the comment")
    comment.body = body
    await db.commit()
    await db.refresh(comment)
    await record_activity(
        db,
        project_id=project_id,
        actor_id=user_id,
        type=ActivityTypeEnum.COMMENT_UPDATED.value,
        message=f"Comment #{comment_id} updated on task #{task_id}",
        task_id=task_id,
    )
    await manager.broadcast_project(project_id, {
        "channel": "comment",
        "event": "updated",
        "project_id": project_id,
        "task_id": task_id,
        "comment": {
            "id": comment.id,
            "author_id": comment.author_id,
            "body": comment.body,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
        }
    })
    await manager.broadcast_task(task_id, {
        "channel": "comment",
        "event": "updated",
        "task_id": task_id,
        "comment_id": comment.id,
    })
    return comment


# PUBLIC_INTERFACE
async def delete_comment(db: AsyncSession, project_id: int, task_id: int, comment_id: int, user_id: int) -> None:
    """Delete a comment. Author can delete; future: project admins can moderate."""
    await _ensure_member_and_task(db, project_id, task_id, user_id)
    result = await db.execute(
        select(Comment).where(
            and_(
                Comment.id == comment_id,
                Comment.project_id == project_id,
                Comment.task_id == task_id,
            )
        )
    )
    comment = result.scalar_one_or_none()
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.author_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can delete the comment")
    await db.execute(
        delete(Comment).where(
            and_(Comment.id == comment_id, Comment.project_id == project_id, Comment.task_id == task_id)
        )
    )
    await db.commit()
    await record_activity(
        db,
        project_id=project_id,
        actor_id=user_id,
        type=ActivityTypeEnum.COMMENT_DELETED.value,
        message=f"Comment #{comment_id} deleted from task #{task_id}",
        task_id=task_id,
    )
    await manager.broadcast_project(project_id, {
        "channel": "comment",
        "event": "deleted",
        "project_id": project_id,
        "task_id": task_id,
        "comment_id": comment_id,
    })
    await manager.broadcast_task(task_id, {
        "channel": "comment",
        "event": "deleted",
        "task_id": task_id,
        "comment_id": comment_id,
    })
