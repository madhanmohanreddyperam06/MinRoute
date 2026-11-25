"""Pydantic schemas for request validation and API responses."""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator


class OptimizationAlgorithm(str, Enum):
    """Supported route optimization algorithms."""

    AUTO = "auto"
    HELD_KARP = "held_karp"
    DIJKSTRA_2OPT = "dijkstra_2opt"
    DIJKSTRA_NN = "dijkstra_nn"
    ASTAR_2OPT = "astar_2opt"
    SIMULATED_ANNEALING = "simulated_annealing"


class DistanceMode(str, Enum):
    """Supported distance computation modes."""

    ROAD = "road"
    HAVERSINE = "haversine"


class CoordinatePoint(BaseModel):
    """Geographic coordinate pair."""

    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")


class LocationInput(BaseModel):
    """Input representation for a warehouse or delivery location."""

    name: str = Field(..., min_length=1, max_length=250, description="Location name or address")
    coordinates: Optional[CoordinatePoint] = Field(
        default=None,
        description="Optional pre-geocoded coordinates; resolved automatically if omitted",
    )

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Location name must not be empty or whitespace")
        return cleaned


class GeocodeRequest(BaseModel):
    """Single-address geocoding request."""

    address: str = Field(..., min_length=1, max_length=250)
    use_cache: bool = True

    @field_validator("address")
    @classmethod
    def clean_address(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Address must not be empty")
        return cleaned


class BatchGeocodeRequest(BaseModel):
    """Batch address geocoding request."""

    addresses: List[str] = Field(..., min_length=1, max_length=50)
    use_cache: bool = True

    @field_validator("addresses")
    @classmethod
    def clean_addresses(cls, values: List[str]) -> List[str]:
        cleaned = [v.strip() for v in values if v and v.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty address is required")
        return cleaned


class GeocodeResponse(BaseModel):
    """Single-address geocoding result."""

    address: str
    success: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    display_name: Optional[str] = None
    source: Optional[str] = None
    error: Optional[str] = None


class BatchGeocodeResponse(BaseModel):
    """Batch geocoding result."""

    results: List[GeocodeResponse]
    resolved_count: int
    total_count: int


class VehicleConfig(BaseModel):
    """Vehicle, speed, fuel, and stop-time configuration."""

    mileage_km_per_liter: float = Field(default=15.0, gt=0.0, le=200.0)
    average_speed_km_per_hour: float = Field(default=40.0, gt=0.0, le=200.0)
    fuel_price_per_liter: float = Field(default=100.0, ge=0.0, le=10000.0)
    stop_time_minutes: float = Field(default=10.0, ge=0.0, le=480.0)
    co2_kg_per_liter: float = Field(default=2.31, ge=0.0, le=20.0)
    currency_symbol: str = Field(default="₹", min_length=1, max_length=5)


class OptimizeRouteRequest(BaseModel):
    """Route optimization request payload."""

    warehouse: LocationInput
    delivery_locations: List[LocationInput] = Field(..., min_length=1, max_length=50)
    algorithm: OptimizationAlgorithm = OptimizationAlgorithm.AUTO
    distance_mode: DistanceMode = DistanceMode.ROAD
    round_trip: bool = True
    include_road_geometry: bool = True
    vehicle: VehicleConfig = Field(default_factory=VehicleConfig)

    @model_validator(mode="after")
    def validate_unique_locations(self) -> "OptimizeRouteRequest":
        wh_key = self.warehouse.name.lower()
        seen: set[str] = set()
        for loc in self.delivery_locations:
            loc_key = loc.name.lower()
            if loc_key == wh_key:
                raise ValueError(
                    f"Delivery location '{loc.name}' cannot be the same as warehouse '{self.warehouse.name}'"
                )
            if loc_key in seen:
                raise ValueError(f"Duplicate delivery location '{loc.name}' is not allowed")
            seen.add(loc_key)
        return self


class CompareAlgorithmsRequest(BaseModel):
    """Multi-algorithm benchmark comparison request payload."""

    warehouse: LocationInput
    delivery_locations: List[LocationInput] = Field(..., min_length=1, max_length=50)
    distance_mode: DistanceMode = DistanceMode.ROAD
    round_trip: bool = True
    vehicle: VehicleConfig = Field(default_factory=VehicleConfig)

    @model_validator(mode="after")
    def validate_unique_locations(self) -> "CompareAlgorithmsRequest":
        wh_key = self.warehouse.name.lower()
        seen: set[str] = set()
        for loc in self.delivery_locations:
            loc_key = loc.name.lower()
            if loc_key == wh_key:
                raise ValueError(
                    f"Delivery location '{loc.name}' cannot be the same as warehouse '{self.warehouse.name}'"
                )
            if loc_key in seen:
                raise ValueError(f"Duplicate delivery location '{loc.name}' is not allowed")
            seen.add(loc_key)
        return self


class RouteSegmentResponse(BaseModel):
    """Single leg of the optimized route."""

    step: int
    from_location: str
    to_location: str
    distance_km: float
    cumulative_distance_km: float
    duration_minutes: float
    path_nodes: List[str]
    geometry: List[Tuple[float, float]]
    is_road_geometry: bool
    is_return_leg: bool


class AnalyticsMetrics(BaseModel):
    """Comprehensive delivery analytics metrics."""

    delivery_count: int
    total_distance_km: float
    baseline_distance_km: float
    distance_saved_km: float
    savings_percentage: float
    distance_per_delivery_km: float
    fuel_liters: float
    fuel_cost: float
    fuel_saved_liters: float
    cost_saved: float
    co2_emissions_kg: float
    co2_saved_kg: float
    travel_time_minutes: float
    stop_time_minutes: float
    total_time_minutes: float
    total_time_hours: float
    efficiency_score: int
    currency_symbol: str


class OptimizeRouteResponse(BaseModel):
    """Full route optimization response."""

    warehouse: str
    algorithm_requested: str
    algorithm_used: str
    algorithm_note: Optional[str] = None
    distance_mode_requested: str
    distance_mode_used: str
    is_round_trip: bool
    optimized_route: List[str]
    nearest_order: List[str]
    total_distance_km: float
    delivery_count: int
    computation_time_ms: float
    coordinates: Dict[str, Tuple[float, float]]
    distance_matrix: Dict[str, Dict[str, float]]
    duration_matrix: Optional[Dict[str, Dict[str, float]]] = None
    segments: List[RouteSegmentResponse]
    analytics: AnalyticsMetrics


class AlgorithmComparisonItem(BaseModel):
    """Single algorithm result inside comparison response."""

    algorithm: str
    label: str
    optimized_route: List[str]
    total_distance_km: float
    distance_saved_km: float
    savings_percentage: float
    travel_time_minutes: float
    fuel_cost: float
    computation_time_ms: float
    note: Optional[str] = None


class CompareAlgorithmsResponse(BaseModel):
    """Side-by-side comparison across supported algorithms."""

    warehouse: str
    distance_mode_used: str
    is_round_trip: bool
    baseline_route: List[str]
    baseline_distance_km: float
    best_algorithm: str
    comparisons: List[AlgorithmComparisonItem]


class AlgorithmInfo(BaseModel):
    """Metadata describing a supported routing algorithm."""

    id: str
    name: str
    description: str
    complexity: str
    exact_optimal: bool
    max_recommended_stops: Optional[int] = None


class HealthResponse(BaseModel):
    """API health status payload."""

    status: str
    app_name: str
    version: str
    algorithms: List[str]


class AnalyticsRecalculateRequest(BaseModel):
    """Request to recalculate delivery analytics with updated vehicle/cost parameters."""

    warehouse: str = Field(..., min_length=1)
    input_delivery_order: List[str] = Field(..., min_length=1)
    optimized_route: List[str] = Field(..., min_length=2)
    total_distance_km: float = Field(..., ge=0.0)
    distance_matrix: Dict[str, Dict[str, float]]
    duration_matrix: Optional[Dict[str, Dict[str, float]]] = None
    round_trip: bool = True
    vehicle: VehicleConfig = Field(default_factory=VehicleConfig)

