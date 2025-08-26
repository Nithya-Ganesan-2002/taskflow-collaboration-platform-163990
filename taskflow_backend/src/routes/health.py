from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/",
    summary="Health Check",
    description="Return a simple health status for the API service.",
    response_model=dict,
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"message": "Healthy"}
                }
            },
        }
    },
)
# PUBLIC_INTERFACE
def health_check() -> dict:
    """Health check endpoint to verify API service is running."""
    return {"message": "Healthy"}
