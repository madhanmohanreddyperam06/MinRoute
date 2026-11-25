"""Unit tests for Dijkstra, A*, 2-Opt, Held-Karp Exact TSP, and Simulated Annealing."""

from backend.models.schemas import OptimizationAlgorithm
from backend.services.graph_builder import Graph, GraphBuilder
from backend.services.optimizer_service import DijkstraOptimizer


def _build_crossing_trap_graph():
    """
    Create a 4-stop square + warehouse where greedy Nearest Neighbor picks a crossing
    suboptimal tour, whereas Held-Karp & 2-Opt find the strictly shorter optimal tour.
    """
    coords = {
        "W": (0.0, 0.0),
        "A": (0.0, 1.0),
        "B": (0.0, 2.0),
        "C": (1.0, 2.0),
        "D": (1.0, 0.0),
    }
    # Construct Euclidean-like matrix (in arbitrary km units)
    import math

    names = list(coords.keys())
    matrix = {u: {} for u in names}
    for u in names:
        for v in names:
            matrix[u][v] = round(math.dist(coords[u], coords[v]) * 10.0, 4)

    return GraphBuilder.build_location_graph(coords, matrix), matrix


def test_dijkstra_sparse_graph_shortest_path():
    g = Graph()
    for n in ["W", "A", "B", "C"]:
        g.add_node(n)
    g.add_edge("W", "A", 2.0)
    g.add_edge("A", "B", 3.0)
    g.add_edge("B", "C", 2.0)
    g.add_edge("W", "C", 20.0)

    opt = DijkstraOptimizer(g)
    dist, path = opt.get_route_between_locations("W", "C")
    assert dist == 7.0
    assert path == ["W", "A", "B", "C"]


def test_astar_matches_dijkstra_optimal_path():
    g = Graph()
    g.add_node("W", (13.0824, 80.2759))
    g.add_node("A", (13.0600, 80.2500))
    g.add_node("B", (13.0418, 80.2337))
    g.add_edge("W", "A", 4.0)
    g.add_edge("A", "B", 3.5)
    g.add_edge("W", "B", 15.0)

    opt = DijkstraOptimizer(g)
    d_dist, d_path = opt.dijkstra_shortest_path("W")["B"]
    a_dist, a_path = opt.astar_shortest_path("W", "B")
    assert a_dist == d_dist == 7.5
    assert a_path == d_path == ["W", "A", "B"]


def test_held_karp_and_two_opt_beat_suboptimal_order():
    graph, _ = _build_crossing_trap_graph()
    opt = DijkstraOptimizer(graph)
    # Give a crossing order intentionally: W -> C -> A -> D -> B
    stops = ["C", "A", "D", "B"]

    hk = opt.optimize_delivery_route("W", stops, algorithm=OptimizationAlgorithm.HELD_KARP, round_trip=True)
    two_opt = opt.optimize_delivery_route("W", stops, algorithm=OptimizationAlgorithm.DIJKSTRA_2OPT, round_trip=True)
    sa = opt.optimize_delivery_route("W", stops, algorithm=OptimizationAlgorithm.SIMULATED_ANNEALING, round_trip=True)
    astar = opt.optimize_delivery_route("W", stops, algorithm=OptimizationAlgorithm.ASTAR_2OPT, round_trip=True)

    # Perimeter of 1x2 rectangle is 10 + 10 + 20 + 20 = 60.0
    assert hk["total_distance"] == 60.0
    assert two_opt["total_distance"] == 60.0
    assert sa["total_distance"] == 60.0
    assert astar["total_distance"] == 60.0
    assert hk["optimized_route"][0] == "W"
    assert hk["optimized_route"][-1] == "W"
    assert set(hk["optimized_route"]) == {"W", "A", "B", "C", "D"}
    assert len(hk["nearest_order"]) == 4


def test_asymmetric_held_karp_vs_one_way():
    coords = {"W": (0.0, 0.0), "A": (0.0, 1.0), "B": (1.0, 0.0)}
    matrix = {
        "W": {"W": 0.0, "A": 1.0, "B": 10.0},
        "A": {"W": 50.0, "A": 0.0, "B": 2.0},
        "B": {"W": 3.0, "A": 50.0, "B": 0.0},
    }
    graph = GraphBuilder.build_location_graph(coords, matrix)
    opt = DijkstraOptimizer(graph)

    rt = opt.optimize_delivery_route("W", ["A", "B"], algorithm=OptimizationAlgorithm.HELD_KARP, round_trip=True)
    assert rt["optimized_route"] == ["W", "A", "B", "W"]
    assert rt["total_distance"] == 6.0

    ow = opt.optimize_delivery_route("W", ["A", "B"], algorithm=OptimizationAlgorithm.HELD_KARP, round_trip=False)
    assert ow["optimized_route"] == ["W", "A", "B"]
    assert ow["total_distance"] == 3.0
    assert ow["is_round_trip"] is False


def test_auto_switches_to_heuristic_above_exact_limit():
    # Build 15 stops (> held_karp_hard_limit=14)
    coords = {"W": (13.0, 80.0)}
    stops = []
    for i in range(15):
        name = f"Stop_{i}"
        stops.append(name)
        coords[name] = (13.0 + i * 0.01, 80.0 + (i % 4) * 0.01)
    from backend.services.distance_service import DistanceService

    matrix = DistanceService.calculate_haversine_matrix(coords)
    graph = GraphBuilder.build_location_graph(coords, matrix)
    opt = DijkstraOptimizer(graph)

    res = opt.optimize_delivery_route("W", stops, algorithm=OptimizationAlgorithm.AUTO, round_trip=True)
    assert res["algorithm_used"] == OptimizationAlgorithm.SIMULATED_ANNEALING.value
    assert res["delivery_count"] == 15
    assert len(res["optimized_route"]) == 17
