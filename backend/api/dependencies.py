"""Shared FastAPI dependency providers for backend services."""

from functools import lru_cache

from backend.core.config import get_settings
from backend.services.analytics_service import AnalyticsService
from backend.services.distance_service import DistanceService
from backend.services.geocoding_service import GeocodingService
from backend.services.road_routing_service import RoadRoutingService


@lru_cache(maxsize=1)
def get_geocoding_service() -> GeocodingService:
    """Return shared GeocodingService instance."""
    return GeocodingService(get_settings())


@lru_cache(maxsize=1)
def get_distance_service() -> DistanceService:
    """Return shared DistanceService instance."""
    return DistanceService(get_settings())


@lru_cache(maxsize=1)
def get_road_routing_service() -> RoadRoutingService:
    """Return shared RoadRoutingService instance."""
    return RoadRoutingService(get_settings())


@lru_cache(maxsize=1)
def get_analytics_service() -> AnalyticsService:
    """Return shared AnalyticsService instance."""
    return AnalyticsService()
