"""Route optimization algorithms: Dijkstra, A*, 2-Opt, Held-Karp Exact TSP, and Simulated Annealing."""

from __future__ import annotations

import heapq
import math
import random
import time
from typing import Dict, List, Optional, Tuple

from backend.core.config import get_settings
from backend.models.schemas import AlgorithmInfo, OptimizationAlgorithm
from backend.services.distance_service import DistanceService
from backend.services.graph_builder import Graph


ALGORITHM_CATALOG: List[AlgorithmInfo] = [
    AlgorithmInfo(
        id=OptimizationAlgorithm.AUTO.value,
        name="Auto (Best Strategy)",
        description=(
            "Uses Held-Karp Exact Dynamic Programming for <= 11 stops (guaranteed optimal) "
            "and compares Dijkstra + 2-Opt vs Simulated Annealing for larger stop counts."
        ),
        complexity="Optimal <= 11 stops; fast heuristic >= 12 stops",
        exact_optimal=True,
        max_recommended_stops=50,
    ),
    AlgorithmInfo(
        id=OptimizationAlgorithm.HELD_KARP.value,
        name="Held-Karp Exact TSP (Dynamic Programming)",
        description=(
            "Finds the mathematically guaranteed shortest Hamiltonian tour over the "
            "Dijkstra shortest-path matrix using bitmask dynamic programming."
        ),
        complexity="O(n^2 * 2^n)",
        exact_optimal=True,
        max_recommended_stops=14,
    ),
    AlgorithmInfo(
        id=OptimizationAlgorithm.DIJKSTRA_2OPT.value,
        name="Dijkstra + Nearest Neighbor + 2-Opt",
        description=(
            "Computes all-pairs shortest paths with Dijkstra's algorithm, constructs an "
            "initial tour via Nearest Neighbor, and eliminates path crossings using 2-Opt local search."
        ),
        complexity="O(V*(V+E)log V + n^3)",
        exact_optimal=False,
        max_recommended_stops=50,
    ),
    AlgorithmInfo(
        id=OptimizationAlgorithm.DIJKSTRA_NN.value,
        name="Dijkstra + Nearest Neighbor (Classic)",
        description=(
            "Original baseline algorithm: Dijkstra shortest-path matrix paired with "
            "greedy Nearest Neighbor stop selection."
        ),
        complexity="O(V*(V+E)log V + n^2)",
        exact_optimal=False,
        max_recommended_stops=50,
    ),
    AlgorithmInfo(
        id=OptimizationAlgorithm.ASTAR_2OPT.value,
        name="A* Shortest Path + 2-Opt",
        description=(
            "Uses A* search with an admissible Haversine geographic heuristic to build "
            "shortest paths, followed by Nearest Neighbor + 2-Opt route refinement."
        ),
        complexity="O(V*(V+E)log V + n^3)",
        exact_optimal=False,
        max_recommended_stops=50,
    ),
    AlgorithmInfo(
        id=OptimizationAlgorithm.SIMULATED_ANNEALING.value,
        name="Dijkstra + Simulated Annealing",
        description=(
            "Stochastic metaheuristic seeded deterministically with 2-Opt reversals and "
            "stop-relocation moves to escape local minima on larger delivery routes."
        ),
        complexity="O(iterations * n)",
        exact_optimal=False,
        max_recommended_stops=50,
    ),
]


class DijkstraOptimizer:
    """
    Route optimizer centered on Dijkstra's shortest-path engine and multiple TSP solvers.
    Supports symmetric and asymmetric (real road) weighted graphs.
    """

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def dijkstra_shortest_path(
        self, start_node: str
    ) -> Dict[str, Tuple[float, List[str]]]:
        """Compute shortest paths from start_node to all nodes using Dijkstra's algorithm."""
        if start_node not in self.graph.nodes:
            raise ValueError(f"Start node '{start_node}' not found in graph")

        distances: Dict[str, float] = {node: float("inf") for node in self.graph.nodes}
        distances[start_node] = 0.0
        previous: Dict[str, Optional[str]] = {node: None for node in self.graph.nodes}

        priority_queue: List[Tuple[float, str]] = [(0.0, start_node)]
        visited = set()

        while priority_queue:
            current_dist, current_node = heapq.heappop(priority_queue)
            if current_node in visited:
                continue
            visited.add(current_node)

            for neighbor, weight in self.graph.get_neighbors(current_node).items():
                if neighbor in visited:
                    continue
                new_dist = current_dist + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current_node
                    heapq.heappush(priority_queue, (new_dist, neighbor))

        paths: Dict[str, Tuple[float, List[str]]] = {}
        for node in self.graph.nodes:
            if distances[node] == float("inf"):
                paths[node] = (float("inf"), [])
            else:
                paths[node] = (distances[node], self._reconstruct_path(previous, node))
        return paths

    def astar_shortest_path(
        self, start_node: str, goal_node: str
    ) -> Tuple[float, List[str]]:
        """Compute shortest path between two nodes using A* with Haversine heuristic."""
        if start_node not in self.graph.nodes or goal_node not in self.graph.nodes:
            raise ValueError("Start or goal node not found in graph")
        if start_node == goal_node:
            return 0.0, [start_node]

        def heuristic(node: str) -> float:
            c1 = self.graph.coordinates.get(node)
            c2 = self.graph.coordinates.get(goal_node)
            if c1 is not None and c2 is not None:
                return DistanceService.calculate_haversine_km(c1, c2)
            return 0.0

        g_score: Dict[str, float] = {node: float("inf") for node in self.graph.nodes}
        g_score[start_node] = 0.0
        previous: Dict[str, Optional[str]] = {node: None for node in self.graph.nodes}
        open_heap: List[Tuple[float, float, str]] = [(heuristic(start_node), 0.0, start_node)]
        closed = set()

        while open_heap:
            _, current_g, current = heapq.heappop(open_heap)
            if current == goal_node:
                return g_score[goal_node], self._reconstruct_path(previous, goal_node)
            if current in closed:
                continue
            closed.add(current)

            for neighbor, weight in self.graph.get_neighbors(current).items():
                if neighbor in closed:
                    continue
                tentative_g = current_g + weight
                if tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    previous[neighbor] = current
                    f_score = tentative_g + heuristic(neighbor)
                    heapq.heappush(open_heap, (f_score, tentative_g, neighbor))

        return float("inf"), []

    @staticmethod
    def _reconstruct_path(
        previous: Dict[str, Optional[str]], end: str
    ) -> List[str]:
        path: List[str] = []
        current: Optional[str] = end
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        return path

    def _compute_all_pairs(
        self, locations: List[str], use_astar: bool = False
    ) -> Dict[str, Dict[str, Tuple[float, List[str]]]]:
        matrix: Dict[str, Dict[str, Tuple[float, List[str]]]] = {}
        if not use_astar:
            for src in locations:
                matrix[src] = self.dijkstra_shortest_path(src)
        else:
            for src in locations:
                matrix[src] = {}
                for dst in locations:
                    matrix[src][dst] = self.astar_shortest_path(src, dst)
        return matrix

    @staticmethod
    def _tour_cost(
        tour: List[str],
        shortest_paths_matrix: Dict[str, Dict[str, Tuple[float, List[str]]]],
        round_trip: bool,
    ) -> float:
        """Compute exact tour cost, correctly handling asymmetric edge weights."""
        if len(tour) <= 1:
            return 0.0
        cost = 0.0
        for idx in range(len(tour) - 1):
            cost += shortest_paths_matrix[tour[idx]][tour[idx + 1]][0]
        if round_trip:
            cost += shortest_paths_matrix[tour[-1]][tour[0]][0]
        return cost

    def _solve_tsp_nearest_neighbor(
        self,
        warehouse: str,
        delivery_locations: List[str],
        shortest_paths_matrix: Dict[str, Dict[str, Tuple[float, List[str]]]],
    ) -> List[str]:
        """Greedy Nearest Neighbor tour starting at warehouse (without closing loop yet)."""
        current = warehouse
        unvisited = list(delivery_locations)
        tour = [warehouse]

        while unvisited:
            nearest_loc = None
            nearest_dist = float("inf")
            for loc in unvisited:
                dist = shortest_paths_matrix[current][loc][0]
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_loc = loc

            if nearest_loc is None or nearest_dist == float("inf"):
                raise ValueError(
                    f"One or more delivery locations are unreachable from '{current}': {unvisited}"
                )

            tour.append(nearest_loc)
            unvisited.remove(nearest_loc)
            current = nearest_loc

        return tour

    def _apply_two_opt(
        self,
        initial_tour: List[str],
        shortest_paths_matrix: Dict[str, Dict[str, Tuple[float, List[str]]]],
        round_trip: bool,
    ) -> List[str]:
        """
        Apply 2-Opt local search preserving index 0 (warehouse).
        Evaluates exact directed tour cost so asymmetric road matrices remain exact.
        """
        n = len(initial_tour)
        if n <= 3:
            return list(initial_tour)

        best_tour = list(initial_tour)
        best_cost = self._tour_cost(best_tour, shortest_paths_matrix, round_trip)

        improved = True
        while improved:
            improved = False
            for i in range(1, n - 1):
                for j in range(i + 1, n):
                    candidate = (
                        best_tour[:i]
                        + list(reversed(best_tour[i : j + 1]))
                        + best_tour[j + 1 :]
                    )
                    candidate_cost = self._tour_cost(
                        candidate, shortest_paths_matrix, round_trip
                    )
                    if candidate_cost + 1e-6 < best_cost:
                        best_tour = candidate
                        best_cost = candidate_cost
                        improved = True
        return best_tour

    def _solve_held_karp(
        self,
        warehouse: str,
        delivery_locations: List[str],
        shortest_paths_matrix: Dict[str, Dict[str, Tuple[float, List[str]]]],
        round_trip: bool,
    ) -> List[str]:
        """Exact TSP solution using Held-Karp bitmask dynamic programming."""
        m = len(delivery_locations)
        if m == 0:
            return [warehouse]
        if m == 1:
            return [warehouse, delivery_locations[0]]

        # Pre-index distances into flat arrays for speed
        dist_wh_to = [shortest_paths_matrix[warehouse][loc][0] for loc in delivery_locations]
        dist_to_wh = [shortest_paths_matrix[loc][warehouse][0] for loc in delivery_locations]
        dist_mat = [
            [shortest_paths_matrix[delivery_locations[i]][delivery_locations[j]][0] for j in range(m)]
            for i in range(m)
        ]

        # dp[(mask, last)] -> (min_cost, prev_index)
        dp: Dict[Tuple[int, int], Tuple[float, int]] = {}
        for i in range(m):
            if dist_wh_to[i] < float("inf"):
                dp[(1 << i, i)] = (dist_wh_to[i], -1)

        full_mask = (1 << m) - 1
        for mask in range(1, full_mask + 1):
            for last in range(m):
                if not (mask & (1 << last)):
                    continue
                state = dp.get((mask, last))
                if state is None:
                    continue
                cur_cost, _ = state

                for nxt in range(m):
                    if mask & (1 << nxt):
                        continue
                    edge_w = dist_mat[last][nxt]
                    if edge_w == float("inf"):
                        continue
                    new_mask = mask | (1 << nxt)
                    new_cost = cur_cost + edge_w
                    prev_best = dp.get((new_mask, nxt))
                    if prev_best is None or new_cost < prev_best[0]:
                        dp[(new_mask, nxt)] = (new_cost, last)

        best_total = float("inf")
        best_last = -1
        for last in range(m):
            state = dp.get((full_mask, last))
            if state is None:
                continue
            total = state[0] + (dist_to_wh[last] if round_trip else 0.0)
            if total < best_total:
                best_total = total
                best_last = last

        if best_last == -1 or best_total == float("inf"):
            raise ValueError("No valid Hamiltonian tour visits all delivery locations.")

        # Reconstruct order
        order_indices: List[int] = []
        mask = full_mask
        curr = best_last
        while curr != -1:
            order_indices.append(curr)
            _, prev_idx = dp[(mask, curr)]
            mask &= ~(1 << curr)
            curr = prev_idx
        order_indices.reverse()

        return [warehouse] + [delivery_locations[idx] for idx in order_indices]

    def _solve_simulated_annealing(
        self,
        warehouse: str,
        delivery_locations: List[str],
        shortest_paths_matrix: Dict[str, Dict[str, Tuple[float, List[str]]]],
        round_trip: bool,
    ) -> List[str]:
        """Deterministic seeded Simulated Annealing with 2-Opt and node relocation moves."""
        nn_tour = self._solve_tsp_nearest_neighbor(
            warehouse, delivery_locations, shortest_paths_matrix
        )
        current_tour = self._apply_two_opt(nn_tour, shortest_paths_matrix, round_trip)
        n = len(current_tour)
        if n <= 3:
            return current_tour

        rng = random.Random(42)
        current_cost = self._tour_cost(current_tour, shortest_paths_matrix, round_trip)
        best_tour = list(current_tour)
        best_cost = current_cost

        temp = max(current_cost * 0.25, 1.0)
        cooling_rate = 0.992
        iterations = min(2500, max(400, n * 120))

        for _ in range(iterations):
            candidate = list(current_tour)
            if rng.random() < 0.65:
                # 2-opt segment reversal
                i, j = sorted(rng.sample(range(1, n), 2))
                candidate[i : j + 1] = reversed(candidate[i : j + 1])
            else:
                # Relocate a single stop
                i, j = rng.sample(range(1, n), 2)
                stop = candidate.pop(i)
                candidate.insert(j, stop)

            cand_cost = self._tour_cost(candidate, shortest_paths_matrix, round_trip)
            delta = cand_cost - current_cost
            if delta < 0 or (temp > 1e-9 and rng.random() < math.exp(-delta / temp)):
                current_tour = candidate
                current_cost = cand_cost
                if current_cost + 1e-6 < best_cost:
                    best_tour = list(current_tour)
                    best_cost = current_cost

            temp *= cooling_rate

        # Final 2-opt polish on best tour found
        return self._apply_two_opt(best_tour, shortest_paths_matrix, round_trip)

    def optimize_delivery_route(
        self,
        warehouse: str,
        delivery_locations: List[str],
        algorithm: OptimizationAlgorithm = OptimizationAlgorithm.AUTO,
        round_trip: bool = True,
    ) -> Dict:
        """
        Optimize delivery route using the chosen strategy.

        Returns dictionary containing:
        - warehouse, optimized_route, nearest_order, total_distance, delivery_count,
          is_round_trip, route_segments, algorithm_used, algorithm_note, computation_time_ms
        """
        start_time = time.perf_counter()

        # Preserve order while deduplicating defensively
        seen = set()
        clean_deliveries: List[str] = []
        for loc in delivery_locations:
            if loc != warehouse and loc not in seen:
                seen.add(loc)
                clean_deliveries.append(loc)

        if not clean_deliveries:
            return {
                "warehouse": warehouse,
                "optimized_route": [warehouse],
                "nearest_order": [],
                "total_distance": 0.0,
                "delivery_count": 0,
                "is_round_trip": False,
                "route_segments": [],
                "algorithm_used": algorithm.value,
                "algorithm_note": None,
                "computation_time_ms": 0.0,
                "shortest_paths_matrix": {},
            }

        settings = get_settings()
        all_locations = [warehouse] + clean_deliveries
        use_astar = algorithm == OptimizationAlgorithm.ASTAR_2OPT
        shortest_paths_matrix = self._compute_all_pairs(all_locations, use_astar=use_astar)

        # Resolve effective algorithm
        chosen = algorithm
        note: Optional[str] = None
        stop_count = len(clean_deliveries)

        if algorithm == OptimizationAlgorithm.AUTO:
            if stop_count <= settings.exact_tsp_auto_limit:
                chosen = OptimizationAlgorithm.HELD_KARP
                note = f"Auto-selected Held-Karp Exact TSP for {stop_count} stops (guaranteed optimal)."
            else:
                chosen = OptimizationAlgorithm.SIMULATED_ANNEALING
                note = (
                    f"Auto-selected Dijkstra + Simulated Annealing for {stop_count} stops "
                    f"(above exact DP limit of {settings.exact_tsp_auto_limit})."
                )
        elif algorithm == OptimizationAlgorithm.HELD_KARP and stop_count > settings.held_karp_hard_limit:
            chosen = OptimizationAlgorithm.DIJKSTRA_2OPT
            note = (
                f"Held-Karp exact DP is capped at {settings.held_karp_hard_limit} stops; "
                f"automatically switched to Dijkstra + 2-Opt for {stop_count} stops."
            )

        # Solve open tour [warehouse, stop_1, ..., stop_k]
        if chosen == OptimizationAlgorithm.HELD_KARP:
            open_tour = self._solve_held_karp(
                warehouse, clean_deliveries, shortest_paths_matrix, round_trip
            )
        elif chosen == OptimizationAlgorithm.DIJKSTRA_NN:
            open_tour = self._solve_tsp_nearest_neighbor(
                warehouse, clean_deliveries, shortest_paths_matrix
            )
        elif chosen in (OptimizationAlgorithm.DIJKSTRA_2OPT, OptimizationAlgorithm.ASTAR_2OPT):
            nn_tour = self._solve_tsp_nearest_neighbor(
                warehouse, clean_deliveries, shortest_paths_matrix
            )
            open_tour = self._apply_two_opt(nn_tour, shortest_paths_matrix, round_trip)
        elif chosen == OptimizationAlgorithm.SIMULATED_ANNEALING:
            sa_tour = self._solve_simulated_annealing(
                warehouse, clean_deliveries, shortest_paths_matrix, round_trip
            )
            two_opt_tour = self._apply_two_opt(
                self._solve_tsp_nearest_neighbor(
                    warehouse, clean_deliveries, shortest_paths_matrix
                ),
                shortest_paths_matrix,
                round_trip,
            )
            sa_cost = self._tour_cost(sa_tour, shortest_paths_matrix, round_trip)
            two_opt_cost = self._tour_cost(two_opt_tour, shortest_paths_matrix, round_trip)
            open_tour = sa_tour if sa_cost <= two_opt_cost else two_opt_tour
        else:
            open_tour = self._solve_tsp_nearest_neighbor(
                warehouse, clean_deliveries, shortest_paths_matrix
            )

        optimized_route = list(open_tour)
        if round_trip:
            optimized_route.append(warehouse)

        # Build segments
        total_distance = 0.0
        route_segments = []
        for idx in range(len(optimized_route) - 1):
            src = optimized_route[idx]
            dst = optimized_route[idx + 1]
            leg_dist, path = shortest_paths_matrix[src][dst]
            total_distance += leg_dist
            route_segments.append(
                {
                    "from": src,
                    "to": dst,
                    "distance": round(leg_dist, 3),
                    "path": path,
                    "is_return_leg": round_trip and idx == len(optimized_route) - 2,
                }
            )

        # Sort stops from nearest to farthest relative to warehouse
        nearest_order = sorted(
            clean_deliveries,
            key=lambda loc: (shortest_paths_matrix[warehouse][loc][0], loc),
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        return {
            "warehouse": warehouse,
            "optimized_route": optimized_route,
            "nearest_order": nearest_order,
            "total_distance": round(total_distance, 3),
            "delivery_count": len(clean_deliveries),
            "is_round_trip": round_trip,
            "route_segments": route_segments,
            "shortest_paths_matrix": shortest_paths_matrix,
            "algorithm_used": chosen.value,
            "algorithm_note": note,
            "computation_time_ms": elapsed_ms,
        }

    def get_route_between_locations(
        self, start: str, end: str
    ) -> Tuple[float, List[str]]:
        """Get shortest path distance and node sequence between two locations."""
        shortest_paths = self.dijkstra_shortest_path(start)
        return shortest_paths.get(end, (float("inf"), []))
