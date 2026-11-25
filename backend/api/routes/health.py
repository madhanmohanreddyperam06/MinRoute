"""Health check endpoints."""

from fastapi import APIRouter

from backend.core.config import get_settings
from backend.models.schemas import HealthResponse, OptimizationAlgorithm

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Check API health")
def health_check() -> HealthResponse:
    """Return service status, version, and available optimization algorithms."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        algorithms=[algo.value for algo in OptimizationAlgorithm],
    )
