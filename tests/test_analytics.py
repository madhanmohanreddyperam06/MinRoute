"""Unit tests for AnalyticsService real baseline comparison and vehicle metrics."""

from backend.models.schemas import VehicleConfig
from backend.services.analytics_service import AnalyticsService


def test_analytics_compares_against_actual_baseline_order():
    service = AnalyticsService()
    matrix = {
        "W": {"W": 0.0, "A": 2.0, "B": 10.0},
        "A": {"W": 2.0, "A": 0.0, "B": 4.0},
        "B": {"W": 10.0, "A": 4.0, "B": 0.0},
    }
    # Input order: W -> B -> A -> W = 10 + 4 + 2 = 16.0
    # Optimized:   W -> A -> B -> W = 2 + 4 + 10 = 16.0 (0 saved)
    # Now make asymmetric so W -> A -> B -> W (10) beats W -> B -> A -> W (20)
    asym_matrix = {
        "W": {"W": 0.0, "A": 2.0, "B": 10.0},
        "A": {"W": 8.0, "A": 0.0, "B": 3.0},
        "B": {"W": 5.0, "A": 5.0, "B": 0.0},
    }
    vehicle = VehicleConfig(
        mileage_km_per_liter=10.0,
        average_speed_km_per_hour=50.0,
        fuel_price_per_liter=100.0,
        stop_time_minutes=10.0,
        co2_kg_per_liter=2.3,
    )
    metrics = service.compute_analytics(
        warehouse="W",
        input_delivery_order=["B", "A"],
        optimized_route=["W", "A", "B", "W"],
        total_distance_km=10.0,
        distance_matrix=asym_matrix,
        vehicle=vehicle,
        round_trip=True,
    )
    assert metrics.baseline_distance_km == 23.0  # 10 + 5 + 8
    assert metrics.total_distance_km == 10.0
    assert metrics.distance_saved_km == 13.0
    assert metrics.fuel_liters == 1.0
    assert metrics.fuel_cost == 100.0
    assert metrics.fuel_saved_liters == 1.3
    assert metrics.cost_saved == 130.0
    assert metrics.travel_time_minutes == 12.0  # 10 / 50 * 60
    assert metrics.stop_time_minutes == 20.0
    assert metrics.total_time_minutes == 32.0
    assert 0 <= metrics.efficiency_score <= 100
