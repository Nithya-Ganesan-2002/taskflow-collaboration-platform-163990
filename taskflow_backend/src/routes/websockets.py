from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from src.websockets.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/ws",
    summary="WebSocket usage help",
    description="Returns usage instructions for WebSocket endpoints.",
    tags=["WebSockets"],
    responses={200: {"description": "Usage instructions"}},
)
# PUBLIC_INTERFACE
def websocket_help() -> dict:
    """Provide usage information for WebSocket clients."""
    return {
        "message": "Use the following endpoints for real-time updates:",
        "endpoints": [
            {
                "path": "/ws/projects/{project_id}",
                "description": "Subscribe to all project-level events (including tasks and comments in the project).",
            },
            {
                "path": "/ws/tasks/{task_id}",
                "description": "Subscribe specifically to a task's events (updates, comments).",
            },
        ],
        "protocol": "WebSocket (ws:// or wss://)",
        "authentication": "Send standard Authorization: Bearer <token> as a WebSocket header when connecting if your client supports it. If not, use a query param token.",
    }


@router.websocket(
    "/ws/projects/{project_id}",
    name="ws_projects",
)
# PUBLIC_INTERFACE
async def ws_projects(websocket: WebSocket, project_id: int, token: str | None = None):
    """
    WebSocket connection for project-level real-time updates.

    Parameters:
    - project_id: The project to subscribe to.
    - token (query param): Optional JWT if your WebSocket client cannot set Authorization header.

    Behavior:
    - On connect, the user is validated. If unauthorized, connection is closed.
    - Client will receive JSON messages for activity/events happening in the project.
    """
    # Try to validate current user via the same dependency. If header isn't available,
    # accept a 'token' query parameter and temporarily set header for dependency.
    try:
        # FastAPI doesn't natively run dependencies in websocket handlers.
        # We'll validate via the same utility by constructing a request-like object.
        # The dependencies.get_current_user expects FastAPI request context; here we decode manually.
        from src.auth.security import decode_token
        auth_header = websocket.headers.get("authorization")
        jwt_token = None
        if auth_header and auth_header.lower().startswith("bearer "):
            jwt_token = auth_header.split(" ", 1)[1]
        elif token:
            jwt_token = token

        if not jwt_token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        payload = decode_token(jwt_token)
        if payload.get("type") != "access":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        user_id = int(payload.get("sub"))
        # Accept connection
        await manager.connect_project(project_id, websocket)
        logger.info("User %s connected to project room %s", user_id, project_id)
        # Initial ack
        await manager.broadcast_project(project_id, {
            "channel": "project",
            "project_id": project_id,
            "event": "connected",
            "actor_id": user_id,
        })
        while True:
            # Keep the socket alive; optional receive loop if client sends pings.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect_project(project_id, websocket)
        logger.info("Project WS disconnected for project %s", project_id)
    except Exception:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.websocket(
    "/ws/tasks/{task_id}",
    name="ws_tasks",
)
# PUBLIC_INTERFACE
async def ws_tasks(websocket: WebSocket, task_id: int, token: str | None = None):
    """
    WebSocket connection for task-level real-time updates.

    Parameters:
    - task_id: The task to subscribe to.
    - token (query param): Optional JWT if your client cannot set Authorization header.

    Behavior:
    - On connect, the user is validated. If unauthorized, connection is closed.
    - Client will receive JSON messages for activity/events happening on this task.
    """
    try:
        from src.auth.security import decode_token
        auth_header = websocket.headers.get("authorization")
        jwt_token = None
        if auth_header and auth_header.lower().startswith("bearer "):
            jwt_token = auth_header.split(" ", 1)[1]
        elif token:
            jwt_token = token

        if not jwt_token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        payload = decode_token(jwt_token)
        if payload.get("type") != "access":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        user_id = int(payload.get("sub"))

        await manager.connect_task(task_id, websocket)
        logger.info("User %s connected to task room %s", user_id, task_id)
        await manager.broadcast_task(task_id, {
            "channel": "task",
            "task_id": task_id,
            "event": "connected",
            "actor_id": user_id,
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect_task(task_id, websocket)
        logger.info("Task WS disconnected for task %s", task_id)
    except Exception:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
