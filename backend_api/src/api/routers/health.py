from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/", summary="Health check", description="Basic health check endpoint.")
def health_check():
    """Health check endpoint.

    Returns:
      - JSON { message: "Healthy" }
    """
    return {"message": "Healthy"}
