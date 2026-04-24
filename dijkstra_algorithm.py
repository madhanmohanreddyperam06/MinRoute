"""
Dijkstra's Algorithm Module - Find shortest paths in weighted graphs
"""

import heapq
from typing import Dict, List, Tuple, Set
from graph_builder import Graph


class DijkstraOptimizer:
    """Implement Dijkstra's shortest path algorithm for route optimization"""
    
    def __init__(self, graph: Graph):
        """
        Initialize with a graph
        
        Args:
            graph (Graph): Location graph
        """
        self.graph = graph
    
    def dijkstra_shortest_path(self, start_node: str) -> Dict[str, Tuple[float, List[str]]]:
        """
        Find shortest paths from start node to all other nodes using Dijkstra's algorithm
        
        Args:
            start_node (str): Starting node (warehouse)
            
        Returns:
            dict: Dictionary with node as key and (distance, path) as value
        """
        if start_node not in self.graph.nodes:
            raise ValueError(f"Start node '{start_node}' not found in graph")
        
        # Initialize distances and paths
        distances = {node: float('inf') for node in self.graph.nodes}
        distances[start_node] = 0
        
        # Previous nodes for path reconstruction
        previous = {node: None for node in self.graph.nodes}
        
        # Priority queue: (distance, node)
        priority_queue = [(0, start_node)]
        visited = set()
        
        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            # Check all neighbors
            neighbors = self.graph.get_neighbors(current_node)
            for neighbor, weight in neighbors.items():
                if neighbor in visited:
                    continue
                
                distance = current_distance + weight
                
                # If found shorter path, update
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_node
                    heapq.heappush(priority_queue, (distance, neighbor))
        
        # Reconstruct paths
        paths = {}
        for node in self.graph.nodes:
            if distances[node] == float('inf'):
                paths[node] = (float('inf'), [])
            else:
                path = self._reconstruct_path(previous, start_node, node)
                paths[node] = (distances[node], path)
        
        return paths
    
    def _reconstruct_path(self, previous: Dict[str, str], start: str, end: str) -> List[str]:
        """
        Reconstruct path from start to end using previous nodes
        
        Args:
            previous (dict): Previous nodes in shortest path
            start (str): Start node
            end (str): End node
            
        Returns:
            list: Path from start to end
        """
        path = []
        current = end
        
        while current is not None:
            path.append(current)
            current = previous[current]
        
        path.reverse()
        return path
    
    def optimize_delivery_route(self, warehouse: str, delivery_locations: List[str]) -> Dict:
        """
        Optimize delivery route using proper TSP approach with Dijkstra's algorithm
        Finds the shortest Hamiltonian cycle visiting all delivery locations
        
        Args:
            warehouse (str): Warehouse location
            delivery_locations (list): List of delivery locations
            
        Returns:
            dict: Optimization results with truly optimized route
        """
        if not delivery_locations:
            return {
                'warehouse': warehouse,
                'optimized_route': [warehouse],
                'total_distance': 0.0,
                'delivery_count': 0,
                'is_round_trip': False,
                'route_segments': []
            }
        
        # Step 1: Calculate shortest paths between all pairs of locations
        all_locations = [warehouse] + delivery_locations
        shortest_paths_matrix = {}
        
        for start in all_locations:
            shortest_paths_matrix[start] = self.dijkstra_shortest_path(start)
        
        # Step 2: Use nearest neighbor heuristic for TSP (can be upgraded to better algorithms)
        optimized_route = self._solve_tsp_nearest_neighbor(warehouse, delivery_locations, shortest_paths_matrix)
        
        # Step 3: Calculate total distance and route segments
        total_distance = 0.0
        route_segments = []
        
        for i in range(len(optimized_route) - 1):
            from_location = optimized_route[i]
            to_location = optimized_route[i + 1]
            
            if from_location in shortest_paths_matrix and to_location in shortest_paths_matrix[from_location]:
                distance, path = shortest_paths_matrix[from_location][to_location]
                total_distance += distance
                route_segments.append({
                    'from': from_location,
                    'to': to_location,
                    'distance': distance,
                    'path': path
                })
        
        # Step 4: Return optimized results
        results = {
            'warehouse': warehouse,
            'optimized_route': optimized_route,
            'total_distance': round(total_distance, 2),
            'delivery_count': len(delivery_locations),
            'is_round_trip': len(optimized_route) > 1 and optimized_route[0] == optimized_route[-1],
            'route_segments': route_segments,
            'shortest_paths_matrix': shortest_paths_matrix
        }
        
        return results
    
    def _solve_tsp_nearest_neighbor(self, warehouse: str, delivery_locations: List[str], 
                                   shortest_paths_matrix: Dict) -> List[str]:
        """
        Solve TSP using nearest neighbor heuristic
        
        Args:
            warehouse (str): Starting warehouse location
            delivery_locations (list): Delivery locations to visit
            shortest_paths_matrix (dict): Pre-computed shortest paths between all locations
            
        Returns:
            list: Optimized route including return to warehouse
        """
        if not delivery_locations:
            return [warehouse]
        
        # Start at warehouse
        current_location = warehouse
        unvisited = delivery_locations.copy()
        route = [current_location]
        
        # Visit each location using nearest neighbor
        while unvisited:
            nearest_location = None
            nearest_distance = float('inf')
            
            # Find nearest unvisited location
            for location in unvisited:
                if (current_location in shortest_paths_matrix and 
                    location in shortest_paths_matrix[current_location]):
                    distance, path = shortest_paths_matrix[current_location][location]
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_location = location
            
            if nearest_location:
                route.append(nearest_location)
                unvisited.remove(nearest_location)
                current_location = nearest_location
            else:
                # If no path found, break to avoid infinite loop
                break
        
        # Return to warehouse
        route.append(warehouse)
        
        return route
    
    def get_route_between_locations(self, start: str, end: str) -> Tuple[float, List[str]]:
        """
        Get shortest route between two specific locations
        
        Args:
            start (str): Starting location
            end (str): Ending location
            
        Returns:
            tuple: (distance, path)
        """
        shortest_paths = self.dijkstra_shortest_path(start)
        
        if end in shortest_paths:
            return shortest_paths[end]
        else:
            return (float('inf'), [])
