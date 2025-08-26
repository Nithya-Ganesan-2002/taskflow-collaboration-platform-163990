from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.core.errors import http_error_handler, validation_exception_handler
from src.core.middleware import LoggingMiddleware
from src.db.init_db import init_db
from src.db.session import get_engine
from src.routes import get_api_router
from src.routes.websockets import router as ws_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    contact={"name": "TaskFlow", "url": "https://example.com"},
    license_info={"name": "Proprietary"},
    openapi_tags=[
        {"name": "Health", "description": "Basic health endpoints"},
        {"name": "Authentication", "description": "User signup, login, and token management"},
        {"name": "Projects", "description": "Project management: CRUD and team membership"},
        {"name": "Tasks", "description": "Task management within projects: CRUD, status, assignment"},
        {"name": "WebSockets", "description": "Real-time communication endpoints"},
        {"name": "Comments", "description": "Task comments APIs"},
        {"name": "Activity", "description": "Project and task activity feed"},
    ],
)

# CORS per request details (allow localhost:3000)
cors_allow_origins: List[str] = (
    settings.BACKEND_CORS_ORIGINS
    if isinstance(settings.BACKEND_CORS_ORIGINS, list)
    else [str(settings.BACKEND_CORS_ORIGINS)]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger middleware
app.add_middleware(LoggingMiddleware)

# Exception handlers
app.add_exception_handler(Exception, http_error_handler)
app.add_exception_handler(Exception, http_error_handler)
from fastapi.exceptions import RequestValidationError  # local import to avoid unused if not needed
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Routers
app.include_router(get_api_router())
# WebSocket and usage help endpoints
app.include_router(ws_router)

@app.on_event("startup")
async def on_startup():
    """Initialize resources on application startup."""
    # Initialize DB (create tables for SQLite default)
    await init_db(get_engine())
