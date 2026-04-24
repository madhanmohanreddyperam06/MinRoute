"""
Distance Calculator Module - Calculate distances between coordinates using Haversine formula
"""

import math
from typing import Tuple


class DistanceCalculator:
    """Handle distance calculations between geographic coordinates"""
    
    EARTH_RADIUS_KM = 6371  # Earth's radius in kilometers
    
    @staticmethod
    def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """
        Calculate the great circle distance between two points on earth using Haversine formula
        
        Args:
            coord1 (tuple): (latitude1, longitude1) in decimal degrees
            coord2 (tuple): (latitude2, longitude2) in decimal degrees
            
        Returns:
            float: Distance in kilometers
        """
        if not coord1 or not coord2:
            return 0.0
        
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Convert decimal degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        distance = DistanceCalculator.EARTH_RADIUS_KM * c
        
        return round(distance, 2)
    
    @staticmethod
    def calculate_distance_matrix(locations: dict) -> dict:
        """
        Calculate distance matrix for multiple locations
        
        Args:
            locations (dict): Dictionary with location names as keys and coordinates as values
            
        Returns:
            dict: Distance matrix where matrix[loc1][loc2] = distance
        """
        location_names = list(locations.keys())
        distance_matrix = {}
        
        for loc1 in location_names:
            distance_matrix[loc1] = {}
            for loc2 in location_names:
                if loc1 == loc2:
                    distance_matrix[loc1][loc2] = 0.0
                else:
                    distance = DistanceCalculator.calculate_distance(
                        locations[loc1], locations[loc2]
                    )
                    distance_matrix[loc1][loc2] = distance
        
        return distance_matrix
    
    @staticmethod
    def get_total_route_distance(route: list, distance_matrix: dict) -> float:
        """
        Calculate total distance for a given route
        
        Args:
            route (list): List of location names in order
            distance_matrix (dict): Distance matrix between all locations
            
        Returns:
            float: Total distance in kilometers
        """
        total_distance = 0.0
        
        for i in range(len(route) - 1):
            current_loc = route[i]
            next_loc = route[i + 1]
            total_distance += distance_matrix[current_loc][next_loc]
        
        return round(total_distance, 2)
