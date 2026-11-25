"""Graph data structure and builder for weighted location networks."""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple


class Graph:
    """Weighted graph supporting symmetric and asymmetric road distances."""

    def __init__(self) -> None:
        self.nodes: Set[str] = set()
        self.edges: Dict[str, Dict[str, float]] = {}
        self.coordinates: Dict[str, Tuple[float, float]] = {}

    def add_node(
        self, node: str, coordinates: Optional[Tuple[float, float]] = None
    ) -> None:
        """Add a node and optional geographic coordinates."""
        self.nodes.add(node)
        if coordinates is not None:
            self.coordinates[node] = coordinates
        if node not in self.edges:
            self.edges[node] = {}

    def add_edge(
        self,
        node1: str,
        node2: str,
        weight: float,
        bidirectional: bool = True,
    ) -> None:
        """Add a weighted edge between existing nodes."""
        if node1 in self.nodes and node2 in self.nodes:
            self.edges[node1][node2] = float(weight)
            if bidirectional:
                self.edges[node2][node1] = float(weight)

    def get_neighbors(self, node: str) -> Dict[str, float]:
        """Return outgoing edges {neighbor: weight} for a node."""
        return self.edges.get(node, {})

    def get_edge_weight(self, node1: str, node2: str) -> float:
        """Return direct edge weight or infinity if no direct edge exists."""
        if node1 == node2:
            return 0.0
        return self.edges.get(node1, {}).get(node2, float("inf"))

    def get_node_count(self) -> int:
        """Return number of nodes in the graph."""
        return len(self.nodes)


class GraphBuilder:
    """Build weighted graphs from coordinates and distance matrices."""

    @staticmethod
    def build_location_graph(
        locations: Dict[str, Tuple[float, float]],
        distance_matrix: Dict[str, Dict[str, float]],
    ) -> Graph:
        """
        Build a complete directed weighted graph preserving asymmetric road weights.
        """
        graph = Graph()

        for location, coords in locations.items():
            graph.add_node(location, coords)

        for loc1 in locations:
            for loc2 in locations:
                if loc1 != loc2:
                    dist = distance_matrix.get(loc1, {}).get(loc2)
                    if dist is not None:
                        graph.add_edge(loc1, loc2, dist, bidirectional=False)

        return graph

    @staticmethod
    def build_warehouse_graph(
        warehouse: str,
        delivery_locations: List[str],
        locations: Dict[str, Tuple[float, float]],
        distance_matrix: Dict[str, Dict[str, float]],
    ) -> Graph:
        """Build a complete graph containing the warehouse and specified delivery stops."""
        subset_names = [warehouse] + [loc for loc in delivery_locations if loc != warehouse]
        subset_locations = {name: locations[name] for name in subset_names if name in locations}
        return GraphBuilder.build_location_graph(subset_locations, distance_matrix)
