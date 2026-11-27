"""Health check endpoint, used by Docker/NGINX to verify liveness."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Simple liveness probe. Does not touch the database on purpose,
    so it stays fast and cheap to call frequently."""
    return {"status": "healthy"}
