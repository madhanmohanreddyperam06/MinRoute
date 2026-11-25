"""Analytics recalculation endpoint."""

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_analytics_service
from backend.models.schemas import AnalyticsMetrics, AnalyticsRecalculateRequest
from backend.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post("", response_model=AnalyticsMetrics, summary="Recalculate route analytics")
def recalculate_analytics(
    payload: AnalyticsRecalculateRequest,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsMetrics:
    """Recalculate fuel, cost, CO2, and time metrics for an existing route."""
    return analytics_service.compute_analytics(
        warehouse=payload.warehouse,
        input_delivery_order=payload.input_delivery_order,
        optimized_route=payload.optimized_route,
        total_distance_km=payload.total_distance_km,
        distance_matrix=payload.distance_matrix,
        vehicle=payload.vehicle,
        round_trip=payload.round_trip,
        duration_matrix=payload.duration_matrix,
    )
