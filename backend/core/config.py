"""Application configuration settings using Pydantic Settings."""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized backend configuration."""

    app_name: str = "Delivery Route Optimization System API"
    app_version: str = "2.0.0"
    api_prefix: str = "/api/v1"
    debug: bool = False

    # Geocoding settings
    nominatim_user_agent: str = "DeliveryRouteOptimizer/2.0 (logistics-route-planner)"
    nominatim_timeout_seconds: float = 10.0
    nominatim_min_interval_seconds: float = 1.1
    photon_api_url: str = "https://photon.komoot.io/api/"

    # Road routing (OSRM) settings
    osrm_base_url: str = "https://router.project-osrm.org"
    osrm_timeout_seconds: float = 4.0

    # Optimization limits
    exact_tsp_auto_limit: int = 12
    held_karp_hard_limit: int = 14

    # Default vehicle & cost parameters
    default_mileage_km_per_liter: float = 15.0
    default_speed_km_per_hour: float = 40.0
    default_fuel_price_per_liter: float = 100.0
    default_stop_time_minutes: float = 10.0
    default_co2_kg_per_liter: float = 2.31
    default_currency_symbol: str = "₹"

    # CORS
    cors_origins: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_prefix="DRO_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
