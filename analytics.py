"""
Analytics Module - Calculate and display delivery analytics
"""

import streamlit as st
import pandas as pd
from typing import Dict, List


class DeliveryAnalytics:
    """Calculate and display delivery route analytics"""
    
    # Constants for calculations
    VEHICLE_MILEAGE_KM_PER_LITER = 15  # Average vehicle mileage
    AVERAGE_SPEED_KM_PER_HOUR = 40     # Average delivery speed
    FUEL_PRICE_PER_LITER = 100         # Average fuel price (can be updated)
    
    def __init__(self):
        """Initialize analytics calculator"""
        pass
    
    def calculate_fuel_consumption(self, total_distance: float) -> Dict[str, float]:
        """
        Calculate fuel consumption and cost
        
        Args:
            total_distance (float): Total delivery distance in km
            
        Returns:
            dict: Fuel consumption metrics
        """
        fuel_liters = total_distance / self.VEHICLE_MILEAGE_KM_PER_LITER
        fuel_cost = fuel_liters * self.FUEL_PRICE_PER_LITER
        
        return {
            'fuel_liters': round(fuel_liters, 2),
            'fuel_cost': round(fuel_cost, 2),
            'mileage': self.VEHICLE_MILEAGE_KM_PER_LITER
        }
    
    def calculate_delivery_time(self, total_distance: float, 
                              delivery_count: int, 
                              stop_time_minutes: int = 10) -> Dict[str, float]:
        """
        Calculate estimated delivery time
        
        Args:
            total_distance (float): Total distance in km
            delivery_count (int): Number of delivery stops
            stop_time_minutes (int): Time per stop in minutes
            
        Returns:
            dict: Time metrics
        """
        # Travel time
        travel_time_hours = total_distance / self.AVERAGE_SPEED_KM_PER_HOUR
        travel_time_minutes = travel_time_hours * 60
        
        # Stop time
        total_stop_time = delivery_count * stop_time_minutes
        
        # Total time
        total_time_minutes = travel_time_minutes + total_stop_time
        total_time_hours = total_time_minutes / 60
        
        return {
            'travel_time_minutes': round(travel_time_minutes, 1),
            'stop_time_minutes': total_stop_time,
            'total_time_minutes': round(total_time_minutes, 1),
            'total_time_hours': round(total_time_hours, 1),
            'average_speed': self.AVERAGE_SPEED_KM_PER_HOUR
        }
    
    def calculate_efficiency_metrics(self, total_distance: float, 
                                   delivery_count: int,
                                   route_optimization: Dict) -> Dict[str, float]:
        """
        Calculate route efficiency metrics
        
        Args:
            total_distance (float): Total optimized distance
            delivery_count (int): Number of deliveries
            route_optimization (dict): Route optimization results
            
        Returns:
            dict: Efficiency metrics
        """
        # Distance per delivery
        distance_per_delivery = total_distance / delivery_count if delivery_count > 0 else 0
        
        # Calculate potential savings (if we had original route)
        original_distance = self._estimate_original_distance(route_optimization)
        distance_savings = original_distance - total_distance
        savings_percentage = (distance_savings / original_distance * 100) if original_distance > 0 else 0
        
        return {
            'distance_per_delivery': round(distance_per_delivery, 2),
            'original_distance_estimate': round(original_distance, 2),
            'distance_savings': round(distance_savings, 2),
            'savings_percentage': round(savings_percentage, 1),
            'delivery_count': delivery_count
        }
    
    def _estimate_original_distance(self, route_optimization: Dict) -> float:
        """
        Estimate what the distance would be without optimization
        
        Args:
            route_optimization (dict): Route optimization results
            
        Returns:
            float: Estimated original distance
        """
        # Simple estimation: assume unoptimized route would be 20-30% longer
        optimized_distance = route_optimization.get('total_distance', 0)
        return optimized_distance * 1.25  # 25% longer estimate
    
    def display_analytics_dashboard(self, total_distance: float, 
                                  delivery_count: int,
                                  route_optimization: Dict = None):
        """
        Display comprehensive analytics dashboard in Streamlit
        
        Args:
            total_distance (float): Total delivery distance
            delivery_count (int): Number of deliveries
            route_optimization (dict): Route optimization results
        """
        st.subheader("📊 Delivery Analytics")
        
        # Calculate all metrics
        fuel_metrics = self.calculate_fuel_consumption(total_distance)
        time_metrics = self.calculate_delivery_time(total_distance, delivery_count)
        efficiency_metrics = self.calculate_efficiency_metrics(
            total_distance, delivery_count, route_optimization or {}
        )
        
        # Create analytics table
        analytics_data = {
            "Metric": [
                "📍 Total Stops",
                "🛣️ Total Distance (km)", 
                "⛽ Fuel Required (L)",
                "💰 Fuel Cost/Litre (₹)",
                "🚗 Travel Time (min)"
            ],
            "Value": [
                delivery_count,
                f"{total_distance:.1f}",
                f"{fuel_metrics['fuel_liters']}",
                f"{fuel_metrics['fuel_cost'] / fuel_metrics['fuel_liters']:.2f}" if fuel_metrics['fuel_liters'] > 0 else "0.00",
                f"{time_metrics['travel_time_minutes']}"
            ]
        }
        
        # Display as table
        df_analytics = pd.DataFrame(analytics_data)
        # Ensure all columns are strings to prevent Arrow serialization errors
        for col in df_analytics.columns:
            df_analytics[col] = df_analytics[col].astype(str)
        st.dataframe(df_analytics, use_container_width=True, hide_index=True)
    
    def _calculate_efficiency_score(self, efficiency_metrics: Dict) -> int:
        """
        Calculate overall efficiency score (0-100)
        
        Args:
            efficiency_metrics (dict): Efficiency metrics
            
        Returns:
            int: Efficiency score
        """
        score = 50  # Base score
        
        # Add points for savings
        savings_pct = efficiency_metrics.get('savings_percentage', 0)
        score += min(savings_pct * 2, 30)  # Max 30 points for savings
        
        # Add points for reasonable distance per delivery
        distance_per_delivery = efficiency_metrics.get('distance_per_delivery', 0)
        if distance_per_delivery < 10:
            score += 20  # Excellent
        elif distance_per_delivery < 20:
            score += 10  # Good
        
        return min(int(score), 100)
