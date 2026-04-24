"""
Graph Builder Module - Construct and manage location graphs for route optimization
"""

from typing import Dict, List, Tuple
import heapq


class Graph:
    """Graph data structure for location network"""
    
    def __init__(self):
        """Initialize an empty graph"""
        self.nodes = set()
        self.edges = {}  # node -> {neighbor: weight}
        self.coordinates = {}  # node -> (lat, lon)
    
    def add_node(self, node: str, coordinates: Tuple[float, float] = None):
        """
        Add a node to the graph
        
        Args:
            node (str): Node name
            coordinates (tuple): (latitude, longitude) coordinates
        """
        self.nodes.add(node)
        if coordinates:
            self.coordinates[node] = coordinates
        if node not in self.edges:
            self.edges[node] = {}
    
    def add_edge(self, node1: str, node2: str, weight: float, bidirectional: bool = True):
        """
        Add an edge between two nodes
        
        Args:
            node1 (str): First node
            node2 (str): Second node
            weight (float): Edge weight (distance)
            bidirectional (bool): Whether to add edge in both directions
        """
        if node1 in self.nodes and node2 in self.nodes:
            self.edges[node1][node2] = weight
            if bidirectional:
                self.edges[node2][node1] = weight
    
    def get_neighbors(self, node: str) -> Dict[str, float]:
        """
        Get neighbors of a node
        
        Args:
            node (str): Node name
            
        Returns:
            dict: Dictionary of neighbors and their weights
        """
        return self.edges.get(node, {})
    
    def get_node_count(self) -> int:
        """Get the number of nodes in the graph"""
        return len(self.nodes)


class GraphBuilder:
    """Build graphs from location data"""
    
    @staticmethod
    def build_location_graph(locations: Dict[str, Tuple[float, float]], 
                           distance_matrix: Dict[str, Dict[str, float]]) -> Graph:
        """
        Build a complete graph from locations and distance matrix
        
        Args:
            locations (dict): Dictionary of location names and coordinates
            distance_matrix (dict): Distance matrix between all locations
            
        Returns:
            Graph: Complete graph with all locations as nodes
        """
        graph = Graph()
        
        # Add all nodes
        for location, coords in locations.items():
            graph.add_node(location, coords)
        
        # Add all edges (complete graph)
        for loc1 in locations:
            for loc2 in locations:
                if loc1 != loc2:
                    distance = distance_matrix[loc1][loc2]
                    graph.add_edge(loc1, loc2, distance)
        
        return graph
    
    @staticmethod
    def build_warehouse_graph(warehouse: str, delivery_locations: List[str],
                            locations: Dict[str, Tuple[float, float]],
                            distance_matrix: Dict[str, Dict[str, float]]) -> Graph:
        """
        Build a graph with warehouse as central node
        
        Args:
            warehouse (str): Warehouse location name
            delivery_locations (list): List of delivery location names
            locations (dict): Dictionary of location names and coordinates
            distance_matrix (dict): Distance matrix between all locations
            
        Returns:
            Graph: Graph with warehouse and delivery locations
        """
        graph = Graph()
        
        # Add warehouse node
        graph.add_node(warehouse, locations[warehouse])
        
        # Add delivery location nodes
        for location in delivery_locations:
            graph.add_node(location, locations[location])
        
        # Add edges between all locations
        all_locations = [warehouse] + delivery_locations
        for i, loc1 in enumerate(all_locations):
            for loc2 in all_locations[i+1:]:
                distance = distance_matrix[loc1][loc2]
                graph.add_edge(loc1, loc2, distance)
        
        return graph
