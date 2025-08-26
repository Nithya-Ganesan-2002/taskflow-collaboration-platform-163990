"""WebSockets related modules for real-time features.

This package exposes:
- manager: singleton WebSocketConnectionManager to manage rooms and broadcasts.
- routes: FastAPI websocket endpoints for projects and tasks.

"""
from .manager import manager, WebSocketConnectionManager  # noqa: F401
