"""Delivery analytics service calculating distance savings, fuel, cost, CO2, time, and efficiency."""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.models.schemas import AnalyticsMetrics, VehicleConfig
from backend.services.distance_service import DistanceService


class AnalyticsService:
    """Compute delivery route KPIs against actual unoptimized baseline order."""

    @staticmethod
    def calculate_fuel_metrics(
        distance_km: float, vehicle: VehicleConfig
    ) -> Dict[str, float]:
        fuel_liters = distance_km / vehicle.mileage_km_per_liter
        fuel_cost = fuel_liters * vehicle.fuel_price_per_liter
        co2_kg = fuel_liters * vehicle.co2_kg_per_liter
        return {
            "fuel_liters": round(fuel_liters, 2),
            "fuel_cost": round(fuel_cost, 2),
            "co2_emissions_kg": round(co2_kg, 2),
        }

    @staticmethod
    def calculate_travel_time_minutes(
        route: List[str],
        total_distance_km: float,
        vehicle: VehicleConfig,
        duration_matrix: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> float:
        """Compute driving time from OSRM duration matrix if available, else speed-based."""
        if duration_matrix and len(route) > 1:
            total_min = 0.0
            valid = True
            for idx in range(len(route) - 1):
                leg_min = duration_matrix.get(route[idx], {}).get(route[idx + 1])
                if leg_min is None:
                    valid = False
                    break
                total_min += leg_min
            if valid:
                return round(total_min, 1)

        return round((total_distance_km / vehicle.average_speed_km_per_hour) * 60.0, 1)

    @staticmethod
    def calculate_efficiency_score(
        savings_percentage: float,
        distance_per_delivery_km: float,
        delivery_count: int,
    ) -> int:
        """Score route efficiency from 0 to 100 based on actual optimization savings and density."""
        if delivery_count <= 0:
            return 0
        score = 55.0
        score += min(max(savings_percentage, 0.0) * 1.5, 25.0)
        if distance_per_delivery_km <= 5.0:
            score += 20.0
        elif distance_per_delivery_km <= 10.0:
            score += 15.0
        elif distance_per_delivery_km <= 20.0:
            score += 10.0
        elif distance_per_delivery_km <= 35.0:
            score += 5.0
        return min(max(int(round(score)), 0), 100)

    def compute_analytics(
        self,
        warehouse: str,
        input_delivery_order: List[str],
        optimized_route: List[str],
        total_distance_km: float,
        distance_matrix: Dict[str, Dict[str, float]],
        vehicle: VehicleConfig,
        round_trip: bool = True,
        duration_matrix: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> AnalyticsMetrics:
        """Compute complete analytics comparing optimized route against user's baseline input order."""
        delivery_count = len(input_delivery_order)

        baseline_route = [warehouse] + list(input_delivery_order)
        if round_trip and input_delivery_order:
            baseline_route.append(warehouse)

        baseline_distance_km = DistanceService.get_total_route_distance(
            baseline_route, distance_matrix
        )

        distance_saved_km = round(baseline_distance_km - total_distance_km, 2)
        if abs(distance_saved_km) < 0.01:
            distance_saved_km = 0.0

        savings_percentage = (
            round((distance_saved_km / baseline_distance_km) * 100.0, 1)
            if baseline_distance_km > 0
            else 0.0
        )

        distance_per_delivery_km = (
            round(total_distance_km / delivery_count, 2) if delivery_count > 0 else 0.0
        )

        opt_fuel = self.calculate_fuel_metrics(total_distance_km, vehicle)
        base_fuel = self.calculate_fuel_metrics(baseline_distance_km, vehicle)

        fuel_saved_liters = round(base_fuel["fuel_liters"] - opt_fuel["fuel_liters"], 2)
        cost_saved = round(base_fuel["fuel_cost"] - opt_fuel["fuel_cost"], 2)
        co2_saved_kg = round(
            base_fuel["co2_emissions_kg"] - opt_fuel["co2_emissions_kg"], 2
        )

        travel_time_minutes = self.calculate_travel_time_minutes(
            optimized_route, total_distance_km, vehicle, duration_matrix
        )
        stop_time_minutes = round(delivery_count * vehicle.stop_time_minutes, 1)
        total_time_minutes = round(travel_time_minutes + stop_time_minutes, 1)
        total_time_hours = round(total_time_minutes / 60.0, 2)

        efficiency_score = self.calculate_efficiency_score(
            savings_percentage=savings_percentage,
            distance_per_delivery_km=distance_per_delivery_km,
            delivery_count=delivery_count,
        )

        return AnalyticsMetrics(
            delivery_count=delivery_count,
            total_distance_km=round(total_distance_km, 2),
            baseline_distance_km=round(baseline_distance_km, 2),
            distance_saved_km=distance_saved_km,
            savings_percentage=savings_percentage,
            distance_per_delivery_km=distance_per_delivery_km,
            fuel_liters=opt_fuel["fuel_liters"],
            fuel_cost=opt_fuel["fuel_cost"],
            fuel_saved_liters=fuel_saved_liters,
            cost_saved=cost_saved,
            co2_emissions_kg=opt_fuel["co2_emissions_kg"],
            co2_saved_kg=co2_saved_kg,
            travel_time_minutes=travel_time_minutes,
            stop_time_minutes=stop_time_minutes,
            total_time_minutes=total_time_minutes,
            total_time_hours=total_time_hours,
            efficiency_score=efficiency_score,
            currency_symbol=vehicle.currency_symbol,
        )
