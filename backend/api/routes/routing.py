"""Route optimization and algorithm benchmarking endpoints."""

from __future__ import annotations

from typing import Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import (
    get_analytics_service,
    get_distance_service,
    get_geocoding_service,
    get_road_routing_service,
)
from backend.core.config import get_settings
from backend.models.schemas import (
    AlgorithmComparisonItem,
    AlgorithmInfo,
    CompareAlgorithmsRequest,
    CompareAlgorithmsResponse,
    LocationInput,
    OptimizationAlgorithm,
    OptimizeRouteRequest,
    OptimizeRouteResponse,
    RouteSegmentResponse,
)
from backend.services.analytics_service import AnalyticsService
from backend.services.distance_service import DistanceService
from backend.services.geocoding_service import GeocodingService
from backend.services.graph_builder import GraphBuilder
from backend.services.optimizer_service import ALGORITHM_CATALOG, DijkstraOptimizer
from backend.services.road_routing_service import RoadRoutingService

router = APIRouter(tags=["Route Optimization"])


def _resolve_coordinates(
    warehouse: LocationInput,
    delivery_locations: List[LocationInput],
    geocoder: GeocodingService,
) -> Tuple[str, List[str], Dict[str, Tuple[float, float]]]:
    """Resolve missing coordinates for warehouse and delivery points."""
    coordinates: Dict[str, Tuple[float, float]] = {}

    for loc in [warehouse, *delivery_locations]:
        if loc.coordinates is not None:
            coordinates[loc.name] = (loc.coordinates.lat, loc.coordinates.lon)
        else:
            geo = geocoder.geocode_address(loc.name)
            if not geo.success or geo.latitude is None or geo.longitude is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=geo.error or f"Could not geocode location '{loc.name}'",
                )
            coordinates[loc.name] = (geo.latitude, geo.longitude)

    delivery_names = [loc.name for loc in delivery_locations]
    return warehouse.name, delivery_names, coordinates


@router.get("/algorithms", response_model=List[AlgorithmInfo], summary="List supported routing algorithms")
def list_algorithms() -> List[AlgorithmInfo]:
    """Return metadata for all available route optimization algorithms."""
    return ALGORITHM_CATALOG


@router.post("/optimize", response_model=OptimizeRouteResponse, summary="Optimize delivery route")
def optimize_route(
    payload: OptimizeRouteRequest,
    geocoder: GeocodingService = Depends(get_geocoding_service),
    distance_service: DistanceService = Depends(get_distance_service),
    road_service: RoadRoutingService = Depends(get_road_routing_service),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> OptimizeRouteResponse:
    """
    Build the location graph, run the selected route optimization algorithm,
    optionally attach road-following geometry, and compute delivery analytics.
    """
    warehouse_name, delivery_names, coordinates = _resolve_coordinates(
        payload.warehouse, payload.delivery_locations, geocoder
    )

    distance_matrix, duration_matrix, distance_mode_used = distance_service.get_matrices(
        coordinates,
        distance_mode=payload.distance_mode,
        average_speed_km_per_hour=payload.vehicle.average_speed_km_per_hour,
    )

    graph = GraphBuilder.build_location_graph(coordinates, distance_matrix)
    optimizer = DijkstraOptimizer(graph)

    try:
        opt_result = optimizer.optimize_delivery_route(
            warehouse=warehouse_name,
            delivery_locations=delivery_names,
            algorithm=payload.algorithm,
            round_trip=payload.round_trip,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    optimized_route: List[str] = opt_result["optimized_route"]
    total_distance_km: float = opt_result["total_distance"]

    use_road_geom = payload.include_road_geometry and distance_mode_used == "road"
    route_waypoints = [coordinates[loc] for loc in optimized_route]
    leg_geometries = road_service.get_multi_leg_geometries(
        route_waypoints,
        use_road_network=use_road_geom,
    )

    segments: List[RouteSegmentResponse] = []
    cumulative_distance = 0.0

    for idx, seg in enumerate(opt_result["route_segments"], start=1):
        src = seg["from"]
        dst = seg["to"]
        leg_dist = float(seg["distance"])
        cumulative_distance = round(cumulative_distance + leg_dist, 3)

        leg_dur = duration_matrix.get(src, {}).get(dst)
        if leg_dur is None:
            leg_dur = round(
                (leg_dist / payload.vehicle.average_speed_km_per_hour) * 60.0, 2
            )

        if idx - 1 < len(leg_geometries):
            geom_points, is_road_geom = leg_geometries[idx - 1]
        else:
            geom_points, is_road_geom = [coordinates[src], coordinates[dst]], False

        segments.append(
            RouteSegmentResponse(
                step=idx,
                from_location=src,
                to_location=dst,
                distance_km=round(leg_dist, 2),
                cumulative_distance_km=round(cumulative_distance, 2),
                duration_minutes=round(leg_dur, 1),
                path_nodes=seg["path"],
                geometry=geom_points,
                is_road_geometry=is_road_geom,
                is_return_leg=bool(seg.get("is_return_leg", False)),
            )
        )

    analytics = analytics_service.compute_analytics(
        warehouse=warehouse_name,
        input_delivery_order=delivery_names,
        optimized_route=optimized_route,
        total_distance_km=total_distance_km,
        distance_matrix=distance_matrix,
        vehicle=payload.vehicle,
        round_trip=payload.round_trip,
        duration_matrix=duration_matrix,
    )

    return OptimizeRouteResponse(
        warehouse=warehouse_name,
        algorithm_requested=payload.algorithm.value,
        algorithm_used=opt_result["algorithm_used"],
        algorithm_note=opt_result.get("algorithm_note"),
        distance_mode_requested=payload.distance_mode.value,
        distance_mode_used=distance_mode_used,
        is_round_trip=opt_result["is_round_trip"],
        optimized_route=optimized_route,
        nearest_order=opt_result["nearest_order"],
        total_distance_km=round(total_distance_km, 2),
        delivery_count=opt_result["delivery_count"],
        computation_time_ms=opt_result["computation_time_ms"],
        coordinates=coordinates,
        distance_matrix=distance_matrix,
        duration_matrix=duration_matrix,
        segments=segments,
        analytics=analytics,
    )


@router.post("/compare", response_model=CompareAlgorithmsResponse, summary="Benchmark all algorithms")
def compare_algorithms(
    payload: CompareAlgorithmsRequest,
    geocoder: GeocodingService = Depends(get_geocoding_service),
    distance_service: DistanceService = Depends(get_distance_service),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> CompareAlgorithmsResponse:
    """Run all applicable optimization algorithms on the same distance matrix and compare metrics."""
    settings = get_settings()
    warehouse_name, delivery_names, coordinates = _resolve_coordinates(
        payload.warehouse, payload.delivery_locations, geocoder
    )

    distance_matrix, duration_matrix, distance_mode_used = distance_service.get_matrices(
        coordinates,
        distance_mode=payload.distance_mode,
        average_speed_km_per_hour=payload.vehicle.average_speed_km_per_hour,
    )

    graph = GraphBuilder.build_location_graph(coordinates, distance_matrix)
    optimizer = DijkstraOptimizer(graph)

    baseline_route = [warehouse_name] + delivery_names
    if payload.round_trip:
        baseline_route.append(warehouse_name)
    baseline_distance = DistanceService.get_total_route_distance(
        baseline_route, distance_matrix
    )

    algo_labels = {item.id: item.name for item in ALGORITHM_CATALOG}
    candidates = [
        OptimizationAlgorithm.DIJKSTRA_NN,
        OptimizationAlgorithm.DIJKSTRA_2OPT,
        OptimizationAlgorithm.ASTAR_2OPT,
        OptimizationAlgorithm.SIMULATED_ANNEALING,
    ]
    if len(delivery_names) <= settings.held_karp_hard_limit:
        candidates.append(OptimizationAlgorithm.HELD_KARP)

    comparisons: List[AlgorithmComparisonItem] = []
    for algo in candidates:
        res = optimizer.optimize_delivery_route(
            warehouse=warehouse_name,
            delivery_locations=delivery_names,
            algorithm=algo,
            round_trip=payload.round_trip,
        )
        analytics = analytics_service.compute_analytics(
            warehouse=warehouse_name,
            input_delivery_order=delivery_names,
            optimized_route=res["optimized_route"],
            total_distance_km=res["total_distance"],
            distance_matrix=distance_matrix,
            vehicle=payload.vehicle,
            round_trip=payload.round_trip,
            duration_matrix=duration_matrix,
        )
        comparisons.append(
            AlgorithmComparisonItem(
                algorithm=algo.value,
                label=algo_labels.get(algo.value, algo.value),
                optimized_route=res["optimized_route"],
                total_distance_km=round(res["total_distance"], 2),
                distance_saved_km=analytics.distance_saved_km,
                savings_percentage=analytics.savings_percentage,
                travel_time_minutes=analytics.travel_time_minutes,
                fuel_cost=analytics.fuel_cost,
                computation_time_ms=res["computation_time_ms"],
                note=res.get("algorithm_note"),
            )
        )

    comparisons.sort(key=lambda item: (item.total_distance_km, item.computation_time_ms))
    best_algo = comparisons[0].algorithm if comparisons else OptimizationAlgorithm.DIJKSTRA_NN.value

    return CompareAlgorithmsResponse(
        warehouse=warehouse_name,
        distance_mode_used=distance_mode_used,
        is_round_trip=payload.round_trip,
        baseline_route=baseline_route,
        baseline_distance_km=round(baseline_distance, 2),
        best_algorithm=best_algo,
        comparisons=comparisons,
    )
