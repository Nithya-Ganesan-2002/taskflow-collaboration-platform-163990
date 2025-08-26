from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Set, Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


@dataclass
class _Room:
    """Represents a set of active connections for a topic (project or task)."""
    connections: Set[WebSocket] = field(default_factory=set)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)
        logger.debug("WebSocket connected. Room size now: %d", len(self.connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.connections:
            self.connections.remove(websocket)
            logger.debug("WebSocket disconnected. Room size now: %d", len(self.connections))

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connections in this room."""
        if not self.connections:
            return
        data = json.dumps(message, default=str)
        send_tasks = []
        # copy to avoid set mutation during iteration
        for ws in list(self.connections):
            send_tasks.append(self._safe_send(ws, data))
        await asyncio.gather(*send_tasks, return_exceptions=True)

    @staticmethod
    async def _safe_send(ws: WebSocket, data: str) -> None:
        try:
            await ws.send_text(data)
        except WebSocketDisconnect:
            # Will be cleaned up by heartbeat or next disconnect event
            pass
        except Exception as e:
            logger.warning("WebSocket send failed: %s", e)


class WebSocketConnectionManager:
    """
    Manages WebSocket connections per project and per task.

    Rooms:
      - project:<project_id>
      - task:<task_id>
    """

    def __init__(self) -> None:
        self._project_rooms: Dict[int, _Room] = {}
        self._task_rooms: Dict[int, _Room] = {}
        self._lock = asyncio.Lock()

    def _get_room(self, container: Dict[int, _Room], key: int) -> _Room:
        room = container.get(key)
        if room is None:
            room = _Room()
            container[key] = room
        return room

    # PUBLIC_INTERFACE
    async def connect_project(self, project_id: int, websocket: WebSocket) -> None:
        """Accept and add the websocket to the project's room."""
        async with self._lock:
            room = self._get_room(self._project_rooms, project_id)
        await room.connect(websocket)

    # PUBLIC_INTERFACE
    async def disconnect_project(self, project_id: int, websocket: WebSocket) -> None:
        """Remove the websocket from the project's room."""
        async with self._lock:
            room = self._project_rooms.get(project_id)
        if room:
            room.disconnect(websocket)

    # PUBLIC_INTERFACE
    async def connect_task(self, task_id: int, websocket: WebSocket) -> None:
        """Accept and add the websocket to the task's room."""
        async with self._lock:
            room = self._get_room(self._task_rooms, task_id)
        await room.connect(websocket)

    # PUBLIC_INTERFACE
    async def disconnect_task(self, task_id: int, websocket: WebSocket) -> None:
        """Remove the websocket from the task's room."""
        async with self._lock:
            room = self._task_rooms.get(task_id)
        if room:
            room.disconnect(websocket)

    # PUBLIC_INTERFACE
    async def broadcast_project(self, project_id: int, payload: dict) -> None:
        """Broadcast a payload to all connections subscribed to the project room."""
        room: Optional[_Room]
        async with self._lock:
            room = self._project_rooms.get(project_id)
        if room:
            await room.broadcast(payload)

    # PUBLIC_INTERFACE
    async def broadcast_task(self, task_id: int, payload: dict) -> None:
        """Broadcast a payload to all connections subscribed to the task room."""
        room: Optional[_Room]
        async with self._lock:
            room = self._task_rooms.get(task_id)
        if room:
            await room.broadcast(payload)


# Singleton manager
manager = WebSocketConnectionManager()
