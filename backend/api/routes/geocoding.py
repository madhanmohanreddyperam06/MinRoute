"""Geocoding API endpoints."""

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_geocoding_service
from backend.models.schemas import (
    BatchGeocodeRequest,
    BatchGeocodeResponse,
    GeocodeRequest,
    GeocodeResponse,
)
from backend.services.geocoding_service import GeocodingService

router = APIRouter(prefix="/geocode", tags=["Geocoding"])


@router.post("", response_model=GeocodeResponse, summary="Geocode a single address")
def geocode_single(
    payload: GeocodeRequest,
    geocoder: GeocodingService = Depends(get_geocoding_service),
) -> GeocodeResponse:
    """Convert an address or 'lat, lon' string into geographic coordinates."""
    return geocoder.geocode_address(payload.address, use_cache=payload.use_cache)


@router.post("/batch", response_model=BatchGeocodeResponse, summary="Geocode multiple addresses")
def geocode_batch(
    payload: BatchGeocodeRequest,
    geocoder: GeocodingService = Depends(get_geocoding_service),
) -> BatchGeocodeResponse:
    """Geocode up to 50 addresses in a single request."""
    results = geocoder.batch_geocode(payload.addresses, use_cache=payload.use_cache)
    resolved_count = sum(1 for item in results if item.success)
    return BatchGeocodeResponse(
        results=results,
        resolved_count=resolved_count,
        total_count=len(results),
    )
