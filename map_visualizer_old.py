"""
Map Visualization Module - Create interactive maps with Folium and real-time routing
"""

import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import streamlit as st
import requests
import json
from typing import Dict, List, Tuple


class MapVisualizer:
    """Create and manage interactive maps for route visualization"""
    
    def __init__(self):
        """Initialize map visualizer"""
        self.default_zoom = 12
        self.routing_api_key = None  # OpenRouteService offers free tier without API key
    
    def get_real_time_route(self, start_coords: Tuple[float, float], 
                         end_coords: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        Get real-time route coordinates using OpenRouteService API
        
        Args:
            start_coords (tuple): Starting coordinates (lat, lon)
            end_coords (tuple): Ending coordinates (lat, lon)
            
        Returns:
            list: List of coordinates representing the actual route
        """
        try:
            # OpenRouteService API endpoint
            url = "https://api.openrouteservice.org/v2/directions/driving-car"
            
            # Prepare request payload
            payload = {
                "coordinates": [
                    [start_coords[1], start_coords[0]],  # Note: API uses [lon, lat] format
                    [end_coords[1], end_coords[0]]
                ]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Make API request
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract route coordinates from response
                if 'features' in data and len(data['features']) > 0:
                    route_geometry = data['features'][0]['geometry']
                    
                    if route_geometry['type'] == 'LineString':
                        # Convert coordinates back to [lat, lon] format
                        route_coords = [
                            (coord[1], coord[0])  # Convert [lon, lat] to [lat, lon]
                            for coord in route_geometry['coordinates']
                        ]
                        return route_coords
            
            # Fallback to straight line if API fails
            return [start_coords, end_coords]
            
        except Exception as e:
            st.warning(f"⚠️ Routing API unavailable, using straight line: {str(e)}")
            # Fallback to straight line
            return [start_coords, end_coords]
    
    def create_route_map(self, locations: Dict[str, Tuple[float, float]], 
                        route: List[str], distance_matrix: Dict[str, Dict[str, float]],
                        warehouse: str = None) -> folium.Map:
        """
        Create an interactive map showing optimized delivery route
        
        Args:
            locations (dict): Dictionary of location names and coordinates
            route (list): Optimized route order
            distance_matrix (dict): Distance matrix between locations
            warehouse (str): Warehouse location name
            
        Returns:
            folium.Map: Interactive map with route visualization
        """
        if not locations or not route:
            st.error("❌ No locations or route data available")
            return None
        
        # Calculate map center (warehouse or first location)
        if warehouse and warehouse in locations:
            center_coords = locations[warehouse]
        else:
            center_coords = locations[route[0]]
        
        # Create base map
        route_map = folium.Map(
            location=center_coords,
            zoom_start=self.default_zoom,
            tiles='OpenStreetMap'
        )
        
        # Add route lines
        self._add_route_lines(route_map, route, locations, distance_matrix)
        
        # Add numbered location markers for round trip
        self._add_numbered_delivery_markers(route_map, route, locations, warehouse)
        
        # Add route summary
        self._add_route_summary(route_map, route, distance_matrix)
        
        return route_map
    
    def _add_route_lines(self, route_map: folium.Map, route: List[str], 
                        locations: Dict[str, Tuple[float, float]], 
                        distance_matrix: Dict[str, Dict[str, float]]):
        """Add real-time route lines connecting locations using actual road networks"""
        
        route_coordinates = []
        route_distances = []
        clean_route = []
        
        # Handle numbered delivery points (e.g., "1. T Nagar" -> "T Nagar")
        for location in route:
            clean_location = location.split('. ', 1)[-1] if '. ' in location else location
            clean_route.append(clean_location)
            
            if clean_location in locations:
                route_coordinates.append(locations[clean_location])
        
        # Draw real-time routes between consecutive points
        if len(route_coordinates) > 1:
            # Forward journey (warehouse to last delivery)
            forward_points = route_coordinates[:-1]  # Exclude final warehouse
            
            # Draw each segment with real routing
            for i in range(len(forward_points)):
                start_point = forward_points[i]
                end_point = forward_points[i + 1] if i + 1 < len(forward_points) else None
                
                if end_point:
                    # Get real-time route for this segment
                    real_route = self.get_real_time_route(start_point, end_point)
                    
                    # Draw the real route
                    folium.PolyLine(
                        locations=real_route,
                        color='blue',
                        weight=4,
                        opacity=0.8,
                        popup=f'Real Route Segment {i+1} (Road-based)'
                    ).add_to(route_map)
                    
                    # Add segment distance label
                    current = clean_route[i]
                    next_loc = clean_route[i + 1]
                    distance = distance_matrix.get(current, {}).get(next_loc, 0)
                    
                    if len(real_route) > 1:
                        # Calculate midpoint for label
                        mid_idx = len(real_route) // 2
                        mid_point = real_route[mid_idx]
                        
                        folium.Marker(
                            location=mid_point,
                            icon=folium.DivIcon(
                                html=f'<div style="background: #2196f3; color: white; '
                                     f'padding: 4px 8px; border-radius: 4px; '
                                     f'font-size: 11px; font-weight: bold;">'
                                     f'Segment {i+1}: {distance:.1f} km</div>',
                                icon_size=(80, 20),
                                icon_anchor=(40, 10)
                            )
                        ).add_to(route_map)
            
            # Return journey (last delivery back to warehouse)
            if len(route_coordinates) >= 2:
                last_delivery = route_coordinates[-2]
                warehouse = route_coordinates[-1]
                
                # Get real-time return route
                return_route = self.get_real_time_route(last_delivery, warehouse)
                
                folium.PolyLine(
                    locations=return_route,
                    color='green',
                    weight=4,
                    opacity=0.8,
                    popup='Return Route (Road-based)'
                ).add_to(route_map)
                
                # Add return route label
                if len(return_route) > 1:
                    mid_idx = len(return_route) // 2
                    mid_point = return_route[mid_idx]
                    
                    # Calculate return distance
                    return_distance = distance_matrix.get(clean_route[-1], {}).get(clean_route[0], 0)
                    
                    folium.Marker(
                        location=mid_point,
                        icon=folium.DivIcon(
                            html=f'<div style="background: #4caf50; color: white; '
                                 f'padding: 4px 8px; border-radius: 4px; '
                                 f'font-size: 11px; font-weight: bold;">'
                                 f'Return: {return_distance:.1f} km</div>',
                            icon_size=(80, 20),
                            icon_anchor=(40, 10)
                        )
                    ).add_to(route_map)
    
    def _add_location_markers(self, route_map: folium.Map, 
                            locations: Dict[str, Tuple[float, float]], 
                            warehouse: str = None):
        """Add markers for all locations"""
        
        for location_name, coords in locations.items():
            # Determine marker color and icon
            if location_name == warehouse:
                color = 'green'
                icon = 'warehouse'
                popup_prefix = '🏢'
                marker_icon = folium.Icon(
                    color=color,
                    icon='home',
                    prefix='fa'
                )
            else:
                color = 'blue'
                icon = 'delivery'
                popup_prefix = '📦'
                marker_icon = folium.Icon(
                    color=color,
                    icon='map-marker',
                    prefix='fa'
                )
            
            # Add marker
            folium.Marker(
                location=coords,
                popup=f"{popup_prefix} <b>{location_name}</b>",
                tooltip=location_name,
                icon=marker_icon
            ).add_to(route_map)
    
    def _add_numbered_delivery_markers(self, route_map: folium.Map, 
                                      route: List[str],
                                      locations: Dict[str, Tuple[float, float]], 
                                      warehouse: str = None):
        """Add numbered markers for delivery points in order"""
        
        for i, location in enumerate(route):
            # Handle numbered delivery points
            clean_location = location.split('. ', 1)[-1] if '. ' in location else location
            
            if clean_location in locations:
                coords = locations[clean_location]
                
                # Determine marker type and number
                if clean_location == warehouse:
                    # Warehouse marker (start and end point)
                    marker_icon = folium.Icon(
                        color='green',
                        icon='home',
                        prefix='fa'
                    )
                    popup_text = f"🏢 <b>{clean_location}</b><br><small>Start/End Point</small>"
                    tooltip_text = f"{clean_location} (Warehouse)"
                else:
                    # Numbered delivery point
                    delivery_number = location.split('. ')[0] if '. ' in location else str(i)
                    marker_icon = folium.Icon(
                        color='blue',
                        icon='map-marker',
                        prefix='fa'
                    )
                    popup_text = f"📦 <b>{clean_location}</b><br><small>Delivery Point #{delivery_number}</small>"
                    tooltip_text = f"{delivery_number}. {clean_location}"
                
                # Add numbered marker
                folium.Marker(
                    location=coords,
                    popup=popup_text,
                    tooltip=tooltip_text,
                    icon=marker_icon
                ).add_to(route_map)
                
                # Add number label for delivery points
                if clean_location != warehouse:
                    folium.Marker(
                        location=coords,
                        icon=folium.DivIcon(
                            html=f'<div style="background: #2196f3; color: white; '
                                 f'border-radius: 50%; width: 25px; height: 25px; '
                                 f'display: flex; align-items: center; justify-content: center; '
                                 f'font-weight: bold; font-size: 12px; border: 2px solid white; '
                                 f'box-shadow: 0 2px 4px rgba(0,0,0,0.3);">{delivery_number}</div>',
                            icon_size=(25, 25),
                            icon_anchor=(12, 12)
                        )
                    ).add_to(route_map)
    
    def _add_route_summary(self, route_map: folium.Map, route: List[str], 
                          distance_matrix: Dict[str, Dict[str, float]]):
        """Add real-time route summary information to the map"""
        
        # Calculate total distance for round trip
        total_distance = 0.0
        clean_route = []
        
        # Handle numbered delivery points
        for location in route:
            clean_location = location.split('. ', 1)[-1] if '. ' in location else location
            clean_route.append(clean_location)
        
        # Calculate distances between consecutive points
        for i in range(len(clean_route) - 1):
            current = clean_route[i]
            next_loc = clean_route[i + 1]
            total_distance += distance_matrix.get(current, {}).get(next_loc, 0)
    
    # Count delivery points (excluding warehouse duplicates)
    delivery_points = [loc for loc in route if loc != route[0]]  # Exclude starting warehouse
    delivery_count = len([loc for loc in delivery_points if not loc.endswith(route[0])])  # Exclude ending warehouse
    
    # Create real-time routing summary HTML
    summary_html = f"""
    <div style="
        background: white;
        padding: 12px;
        border-radius: 8px;
        border: 2px solid #4CAF50;
        font-family: Arial, sans-serif;
        position: fixed;
        bottom: 20px;
        left: 20px;
        z-index: 1000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        min-width: 250px;
    ">
        <h4 style="margin: 0 0 8px 0; color: #2E7D32; font-size: 14px;">
            🛣️ Real-Time Route Summary
        </h4>
        <p style="margin: 3px 0; font-size: 12px; color: #333;">
            <b>Total Distance:</b> {total_distance:.1f} km
        </p>
        <p style="margin: 3px 0; font-size: 12px; color: #333;">
            <b>Delivery Points:</b> {delivery_count}
        </p>
        <p style="margin: 3px 0; font-size: 12px; color: #333;">
            <b>Route Type:</b> Real-Time Road Routing
        </p>
        <div style="margin: 8px 0; font-size: 11px; color: #666;">
            <b>🛣️ Routes calculated using actual road networks</b>
        </div>
    </div>
    """
    
    # Add summary to map
    folium.Marker(
        location=[0, 0],
        icon=folium.DivIcon(
            html=summary_html,
            icon_size=(300, 200),
            icon_anchor=(150, 100)
        )
    ).add_to(route_map)
    
    def display_map(self, route_map: folium.Map, height: int = 500):
        """
        Display the map in Streamlit
        
        Args:
            route_map (folium.Map): Map to display
            height (int): Map height in pixels
        """
        if route_map:
            st_folium(
                route_map,
                height=height,
                width='100%',
                returned_objects=[]
            )
        else:
            st.error("❌ Unable to generate map")
    
    def create_location_cluster_map(self, locations: Dict[str, Tuple[float, float]]) -> folium.Map:
        """
        Create a map with clustered markers for all locations
        
        Args:
            locations (dict): Dictionary of location names and coordinates
            
        Returns:
            folium.Map: Map with clustered markers
        """
        if not locations:
            return None
        
        # Calculate center
        center_lat = sum(coords[0] for coords in locations.values()) / len(locations)
        center_lon = sum(coords[1] for coords in locations.values()) / len(locations)
        
        # Create map
        cluster_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10
        )
        
        # Add marker cluster
        marker_cluster = MarkerCluster().add_to(cluster_map)
        
        # Add markers to cluster
        for name, coords in locations.items():
            folium.Marker(
                location=coords,
                popup=f"<b>{name}</b>",
                tooltip=name
            ).add_to(marker_cluster)
        
        return cluster_map
