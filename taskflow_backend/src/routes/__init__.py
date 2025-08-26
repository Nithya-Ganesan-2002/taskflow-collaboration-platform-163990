from fastapi import APIRouter

from .health import router as health_router

# PUBLIC_INTERFACE
def get_api_router() -> APIRouter:
    """Build and return the root API router with all included sub-routers."""
    api_router = APIRouter()
    api_router.include_router(health_router, tags=["Health"])
    return api_router
