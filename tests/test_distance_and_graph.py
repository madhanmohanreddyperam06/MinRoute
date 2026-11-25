"""Unit tests for Haversine calculations, OSRM matrix fallback, and GraphBuilder."""

from unittest.mock import Mock

from backend.models.schemas import DistanceMode
from backend.services.distance_service import DistanceService
from backend.services.graph_builder import Graph, GraphBuilder


def test_haversine_known_distance_and_antipodal_safety():
    # Identical coordinates -> 0.0
    assert DistanceService.calculate_haversine_km((13.0827, 80.2707), (13.0827, 80.2707)) == 0.0

    # Antipodal points must not trigger ValueError in math.asin due to float precision
    antipodal = DistanceService.calculate_haversine_km((0.0, 0.0), (0.0, 180.0))
    assert 20000.0 <= antipodal <= 20020.0

    # Chennai Central to T Nagar (~5-6 km straight line)
    dist = DistanceService.calculate_haversine_km((13.0824, 80.2759), (13.0418, 80.2337))
    assert 5.0 <= dist <= 7.5


def test_haversine_matrix_symmetry_and_total_route():
    coords = {
        "A": (13.0824, 80.2759),
        "B": (13.0418, 80.2337),
        "C": (12.9816, 80.2186),
    }
    matrix = DistanceService.calculate_haversine_matrix(coords)
    assert matrix["A"]["A"] == 0.0
    assert matrix["A"]["B"] == matrix["B"]["A"]
    total = DistanceService.get_total_route_distance(["A", "B", "C", "A"], matrix)
    expected = round(matrix["A"]["B"] + matrix["B"]["C"] + matrix["C"]["A"], 3)
    assert total == expected


def test_osrm_table_api_success_and_fallback(monkeypatch):
    coords = {
        "Warehouse": (13.0824, 80.2759),
        "Stop1": (13.0418, 80.2337),
    }
    service = DistanceService()

    # Asymmetric mock OSRM table response
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "code": "Ok",
        "distances": [[0.0, 8400.0], [9100.0, 0.0]],
        "durations": [[0.0, 900.0], [1020.0, 0.0]],
    }
    monkeypatch.setattr("backend.services.distance_service.requests.get", lambda *a, **kw: mock_resp)

    dist_m, dur_m, mode = service.get_matrices(coords, DistanceMode.ROAD)
    assert mode == "road"
    assert dist_m["Warehouse"]["Stop1"] == 8.4
    assert dist_m["Stop1"]["Warehouse"] == 9.1
    assert dur_m["Warehouse"]["Stop1"] == 15.0
    assert dur_m["Stop1"]["Warehouse"] == 17.0

    # Verify fallback to Haversine when OSRM fails
    def raise_err(*a, **kw):
        raise ConnectionError("offline")

    monkeypatch.setattr("backend.services.distance_service.requests.get", raise_err)
    dist_fb, dur_fb, mode_fb = service.get_matrices(coords, DistanceMode.ROAD)
    assert mode_fb == "haversine"
    assert dist_fb["Warehouse"]["Stop1"] == dist_fb["Stop1"]["Warehouse"]
    assert dur_fb["Warehouse"]["Stop1"] > 0


def test_graph_builder_preserves_asymmetric_weights():
    coords = {"W": (0.0, 0.0), "A": (0.0, 1.0), "B": (1.0, 0.0)}
    matrix = {
        "W": {"W": 0.0, "A": 5.0, "B": 10.0},
        "A": {"W": 8.0, "A": 0.0, "B": 3.0},
        "B": {"W": 4.0, "A": 7.0, "B": 0.0},
    }
    graph: Graph = GraphBuilder.build_location_graph(coords, matrix)
    assert graph.get_node_count() == 3
    assert graph.get_edge_weight("W", "A") == 5.0
    assert graph.get_edge_weight("A", "W") == 8.0
