"""Frontend configuration, sample route presets, and UI constants."""

from __future__ import annotations

import os
from typing import Dict, List


BACKEND_URL: str = os.getenv("DRO_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

ALGORITHM_OPTIONS: Dict[str, str] = {
    "auto": "Auto (Best Strategy)",
    "held_karp": "Held-Karp Exact TSP (Optimal <= 14 stops)",
    "dijkstra_2opt": "Dijkstra + Nearest Neighbor + 2-Opt",
    "dijkstra_nn": "Dijkstra + Nearest Neighbor (Classic)",
    "astar_2opt": "A* Shortest Path + 2-Opt",
    "simulated_annealing": "Dijkstra + Simulated Annealing",
}

DISTANCE_MODE_OPTIONS: Dict[str, str] = {
    "road": "Real Road Network (OSRM)",
    "haversine": "Straight-Line (Haversine Formula)",
}

SAMPLE_PRESETS: Dict[str, Dict] = {
    "Chennai Logistics Demo": {
        "warehouse": {"name": "Chennai Central", "lat": 13.0824, "lon": 80.2759},
        "deliveries": [
            {"name": "T Nagar, Chennai", "lat": 13.0418, "lon": 80.2337},
            {"name": "Adyar, Chennai", "lat": 13.0012, "lon": 80.2565},
            {"name": "Velachery, Chennai", "lat": 12.9816, "lon": 80.2186},
            {"name": "Anna Nagar, Chennai", "lat": 13.0850, "lon": 80.2101},
        ],
    },
    "Mumbai Metro Demo": {
        "warehouse": {"name": "Mumbai Port", "lat": 18.9532, "lon": 72.8482},
        "deliveries": [
            {"name": "Dadar, Mumbai", "lat": 19.0178, "lon": 72.8478},
            {"name": "Bandra, Mumbai", "lat": 19.0596, "lon": 72.8295},
            {"name": "Andheri, Mumbai", "lat": 19.1136, "lon": 72.8697},
            {"name": "Powai, Mumbai", "lat": 19.1176, "lon": 72.9060},
        ],
    },
    "Delhi NCR Demo": {
        "warehouse": {"name": "Connaught Place, New Delhi", "lat": 28.6315, "lon": 77.2167},
        "deliveries": [
            {"name": "Noida", "lat": 28.5355, "lon": 77.3910},
            {"name": "Gurugram", "lat": 28.4595, "lon": 77.0266},
            {"name": "Dwarka, New Delhi", "lat": 28.5921, "lon": 77.0460},
            {"name": "Rohini, New Delhi", "lat": 28.7495, "lon": 77.0565},
        ],
    },
}

DEFAULT_VEHICLE_CONFIG: Dict[str, object] = {
    "mileage_km_per_liter": 15.0,
    "average_speed_km_per_hour": 40.0,
    "fuel_price_per_liter": 100.0,
    "stop_time_minutes": 10.0,
    "co2_kg_per_liter": 2.31,
    "currency_symbol": "₹",
}
