"""
Geocoding Module - Convert addresses to coordinates with fallback services
"""

import time
import random
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import streamlit as st
import json


class Geocoder:
    """Handle geocoding operations with fallback services and caching"""
    
    def __init__(self):
        """Initialize geocoder with fallback capabilities"""
        # Predefined coordinate cache for common Indian locations
        self.coordinate_cache = {
            'chennai': (13.0827, 80.2707),
            't nagar': (13.0418, 80.2337),
            'madhavaram': (13.1429, 80.2325),
            'perambur': (13.1166, 80.2316),
            'puzhal': (13.1345, 80.2033),
            'red hills': (13.1667, 80.1833),
            'adyar': (13.0067, 80.2085),
            'velachery': (12.9816, 80.2186),
            'ambattur': (13.0808, 80.2125),
            'tambaram': (13.0734, 80.2625),
            'mumbai': (19.0760, 72.8777),
            'delhi': (28.6139, 77.2090),
            'bangalore': (12.9716, 77.5946),
            'kolkata': (22.5726, 88.3639),
            'chennai central': (13.0827, 80.2707),
            'chennai port': (13.0846, 80.2844),
            'chennai airport': (12.9844, 80.1745),
        }
        
        self.nominatim = None
        self.last_request_time = 0
        self.min_request_interval = 3.0  # Increased to 3 seconds
    
    def _get_cached_coordinates(self, address: str) -> tuple:
        """Get coordinates from cache if available"""
        # Normalize address for cache lookup
        normalized_address = address.lower().strip()
        
        # Check exact match
        if normalized_address in self.coordinate_cache:
            coords = self.coordinate_cache[normalized_address]
            print(f"  📋 Cache hit: {coords}")
            return coords
        
        # Check partial match
        for cached_addr, coords in self.coordinate_cache.items():
            if cached_addr in normalized_address or normalized_address in cached_addr:
                print(f"  📋 Partial cache hit: {coords}")
                return coords
        
        return None
    
    def geocode_address(self, address: str, max_retries: int = 2) -> tuple:
        """
        Convert address to latitude and longitude coordinates with caching and fallbacks
        
        Args:
            address (str): Address to geocode
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            tuple: (latitude, longitude) or None if not found
        """
        if not address or not address.strip():
            print("⚠️ Empty address provided")
            return None
        
        print(f"🔍 Geocoding address: '{address}'")
        
        # Try cache first
        cached_coords = self._get_cached_coordinates(address)
        if cached_coords:
            return cached_coords
        
        # Initialize Nominatim with random user agent to avoid conflicts
        if not self.nominatim:
            self.nominatim = Nominatim(user_agent=f"delivery_optimizer_{random.randint(10000, 99999)}")
        
        for attempt in range(max_retries):
            try:
                # Respect rate limits
                self._respect_rate_limit()
                
                print(f"  Attempt {attempt + 1}/{max_retries}")
                
                location = self.nominatim.geocode(address, timeout=15)
                
                print(f"  Raw response: {location}")
                
                if location:
                    coords = (location.latitude, location.longitude)
                    print(f"  ✅ Success: {coords}")
                    return coords
                else:
                    print(f"  ❌ No location found for: {address}")
                    
            except GeocoderTimedOut as e:
                print(f"  ⏰ Timeout: {e}")
                if attempt == max_retries - 1:
                    print("  ❌ Final timeout reached")
                continue
            except GeocoderServiceError as e:
                print(f"  🌐 Service error: {e}")
                if attempt == max_retries - 1:
                    print("  ❌ Final service error - using fallback")
                    return self._fallback_geocode(address)
                continue
            except Exception as e:
                print(f"  ❌ Unexpected error: {e}")
                if attempt == max_retries - 1:
                    print("  ❌ Final error reached - using fallback")
                    return self._fallback_geocode(address)
                continue
        
        print(f"  ❌ All attempts failed for: {address}")
        return self._fallback_geocode(address)
    
    def _respect_rate_limit(self):
        """Ensure minimum interval between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(f"  ⏱️ Rate limiting: sleeping {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _fallback_geocode(self, address: str) -> tuple:
        """
        Fallback geocoding using simple pattern matching and coordinates
        
        Args:
            address (str): Address to geocode
            
        Returns:
            tuple: (latitude, longitude) or None if not found
        """
        print("  🔄 Using fallback geocoding...")
        
        # Normalize address
        normalized_address = address.lower().strip()
        
        # Try to extract coordinates from known patterns
        if 'chennai' in normalized_address:
            if 'central' in normalized_address or 'center' in normalized_address:
                return self.coordinate_cache['chennai central']
            elif 'port' in normalized_address:
                return self.coordinate_cache['chennai port']
            elif 'airport' in normalized_address:
                return self.coordinate_cache['chennai airport']
            else:
                return self.coordinate_cache['chennai']
        
        # Check other cities
        for city in ['mumbai', 'delhi', 'bangalore', 'kolkata']:
            if city in normalized_address:
                return self.coordinate_cache[city]
        
        # Check Chennai areas
        for area in ['t nagar', 'madhavaram', 'perambur', 'puzhal', 'red hills', 'adyar', 'velachery', 'ambattur', 'tambaram']:
            if area in normalized_address:
                return self.coordinate_cache[area]
        
        print(f"  ❌ No fallback coordinates found for: {address}")
        return None
    
    def batch_geocode(self, addresses: list) -> dict:
        """
        Geocode multiple addresses
        
        Args:
            addresses (list): List of addresses to geocode
            
        Returns:
            dict: Dictionary with address as key and coordinates as value
        """
        results = {}
        
        with st.spinner("🔄 Converting addresses to coordinates..."):
            for address in addresses:
                coords = self.geocode_address(address)
                if coords:
                    results[address] = coords
                else:
                    results[address] = None
        
        return results
