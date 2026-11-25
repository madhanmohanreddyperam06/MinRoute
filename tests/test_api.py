"""FastAPI integration tests covering health, geocoding, optimize, compare, and analytics endpoints."""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_and_algorithms_endpoints():
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "healthy"
    assert "held_karp" in body["algorithms"]
    assert "dijkstra_nn" in body["algorithms"]

    algos = client.get("/api/v1/algorithms")
    assert algos.status_code == 200
    algo_ids = {item["id"] for item in algos.json()}
    assert {"auto", "held_karp", "dijkstra_2opt", "dijkstra_nn", "astar_2opt", "simulated_annealing"}.issubset(algo_ids)


def test_geocode_direct_coordinates_and_batch():
    single = client.post("/api/v1/geocode", json={"address": "13.0824, 80.2759"})
    assert single.status_code == 200
    assert single.json()["success"] is True
    assert single.json()["latitude"] == 13.0824

    batch = client.post(
        "/api/v1/geocode/batch",
        json={"addresses": ["13.0824, 80.2759", "13.0418, 80.2337"]},
    )
    assert batch.status_code == 200
    assert batch.json()["resolved_count"] == 2


def test_optimize_compare_and_recalculate_endpoints():
    payload = {
        "warehouse": {"name": "Chennai Central", "coordinates": {"lat": 13.0824, "lon": 80.2759}},
        "delivery_locations": [
            {"name": "T Nagar", "coordinates": {"lat": 13.0418, "lon": 80.2337}},
            {"name": "Adyar", "coordinates": {"lat": 13.0012, "lon": 80.2565}},
            {"name": "Velachery", "coordinates": {"lat": 12.9816, "lon": 80.2186}},
        ],
        "algorithm": "auto",
        "distance_mode": "haversine",
        "round_trip": True,
        "include_road_geometry": False,
    }

    opt = client.post("/api/v1/optimize", json=payload)
    assert opt.status_code == 200
    opt_data = opt.json()
    assert opt_data["algorithm_used"] == "held_karp"
    assert opt_data["delivery_count"] == 3
    assert opt_data["is_round_trip"] is True
    assert len(opt_data["segments"]) == 4
    assert len(opt_data["nearest_order"]) == 3
    assert opt_data["analytics"]["total_distance_km"] == opt_data["total_distance_km"]

    # Compare endpoint
    cmp_payload = {
        "warehouse": payload["warehouse"],
        "delivery_locations": payload["delivery_locations"],
        "distance_mode": "haversine",
        "round_trip": True,
    }
    cmp_resp = client.post("/api/v1/compare", json=cmp_payload)
    assert cmp_resp.status_code == 200
    cmp_data = cmp_resp.json()
    assert len(cmp_data["comparisons"]) == 5
    assert cmp_data["best_algorithm"] in {"held_karp", "dijkstra_2opt", "astar_2opt", "simulated_annealing", "dijkstra_nn"}

    # Analytics recalculate endpoint
    recalc_resp = client.post(
        "/api/v1/analytics",
        json={
            "warehouse": opt_data["warehouse"],
            "input_delivery_order": ["T Nagar", "Adyar", "Velachery"],
            "optimized_route": opt_data["optimized_route"],
            "total_distance_km": opt_data["total_distance_km"],
            "distance_matrix": opt_data["distance_matrix"],
            "round_trip": True,
            "vehicle": {
                "mileage_km_per_liter": 20.0,
                "average_speed_km_per_hour": 40.0,
                "fuel_price_per_liter": 120.0,
                "stop_time_minutes": 5.0,
                "co2_kg_per_liter": 2.31,
                "currency_symbol": "$",
            },
        },
    )
    assert recalc_resp.status_code == 200
    assert recalc_resp.json()["currency_symbol"] == "$"
    assert recalc_resp.json()["stop_time_minutes"] == 15.0


def test_optimize_rejects_duplicate_and_warehouse_stops():
    dup = client.post(
        "/api/v1/optimize",
        json={
            "warehouse": {"name": "Depot", "coordinates": {"lat": 13.0, "lon": 80.0}},
            "delivery_locations": [
                {"name": "Stop A", "coordinates": {"lat": 13.1, "lon": 80.1}},
                {"name": "stop a", "coordinates": {"lat": 13.2, "lon": 80.2}},
            ],
        },
    )
    assert dup.status_code == 422

    same_as_wh = client.post(
        "/api/v1/optimize",
        json={
            "warehouse": {"name": "Depot", "coordinates": {"lat": 13.0, "lon": 80.0}},
            "delivery_locations": [
                {"name": "Depot", "coordinates": {"lat": 13.0, "lon": 80.0}},
            ],
        },
    )
    assert same_as_wh.status_code == 422
