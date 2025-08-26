from fastapi import APIRouter

from .health import router as health_router
from .auth import router as auth_router
from .projects import router as projects_router
from .tasks import router as tasks_router
from .comments import router as comments_router
from .activity import router as activity_router

# PUBLIC_INTERFACE
def get_api_router() -> APIRouter:
    """Build and return the root API router with all included sub-routers."""
    api_router = APIRouter()
    api_router.include_router(health_router, tags=["Health"])
    api_router.include_router(auth_router, tags=["Authentication"])
    api_router.include_router(projects_router, tags=["Projects"])
    api_router.include_router(tasks_router, tags=["Tasks"])
    api_router.include_router(comments_router, tags=["Comments"])
    api_router.include_router(activity_router, tags=["Activity"])
    return api_router
