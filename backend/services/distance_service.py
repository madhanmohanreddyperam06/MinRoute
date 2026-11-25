"""Distance and travel-duration matrix service (OSRM road network + Haversine)."""

from __future__ import annotations

import logging
import math
from typing import Dict, List, Optional, Tuple

import requests

from backend.core.config import Settings, get_settings
from backend.models.schemas import DistanceMode

logger = logging.getLogger(__name__)


class DistanceService:
    """Compute pairwise distances and travel durations across geographic locations."""

    EARTH_RADIUS_KM = 6371.0

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    @classmethod
    def calculate_haversine_km(
        cls, coord1: Tuple[float, float], coord2: Tuple[float, float]
    ) -> float:
        """
        Calculate great-circle distance between two (lat, lon) points in kilometers.
        Clamps intermediate term to [0, 1] to prevent floating-point domain errors.
        """
        if not coord1 or not coord2:
            return 0.0

        lat1, lon1 = coord1
        lat2, lon2 = coord2
        if lat1 == lat2 and lon1 == lon2:
            return 0.0

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2.0) ** 2
        )
        a_clamped = min(1.0, max(0.0, a))
        c = 2.0 * math.asin(math.sqrt(a_clamped))
        return round(cls.EARTH_RADIUS_KM * c, 3)

    @classmethod
    def calculate_haversine_matrix(
        cls, locations: Dict[str, Tuple[float, float]]
    ) -> Dict[str, Dict[str, float]]:
        """Compute symmetric Haversine distance matrix (km) for all named locations."""
        names = list(locations.keys())
        matrix: Dict[str, Dict[str, float]] = {name: {} for name in names}
        for i, loc1 in enumerate(names):
            matrix[loc1][loc1] = 0.0
            for j in range(i + 1, len(names)):
                loc2 = names[j]
                dist = cls.calculate_haversine_km(locations[loc1], locations[loc2])
                matrix[loc1][loc2] = dist
                matrix[loc2][loc1] = dist
        return matrix

    @classmethod
    def calculate_duration_matrix_from_distances(
        cls,
        distance_matrix: Dict[str, Dict[str, float]],
        average_speed_km_per_hour: float = 40.0,
    ) -> Dict[str, Dict[str, float]]:
        """Derive travel duration matrix (minutes) from distance matrix and speed."""
        speed = max(average_speed_km_per_hour, 1.0)
        durations: Dict[str, Dict[str, float]] = {}
        for loc1, row in distance_matrix.items():
            durations[loc1] = {
                loc2: round((dist / speed) * 60.0, 2) if loc1 != loc2 else 0.0
                for loc2, dist in row.items()
            }
        return durations

    def fetch_osrm_matrices(
        self,
        locations: Dict[str, Tuple[float, float]],
        fallback_speed_kmh: float = 40.0,
    ) -> Tuple[Optional[Dict[str, Dict[str, float]]], Optional[Dict[str, Dict[str, float]]]]:
        """
        Fetch pairwise driving distances (km) and durations (minutes) via OSRM Table API.
        Returns (None, None) if OSRM is unavailable or rejects the request.
        """
        names = list(locations.keys())
        if len(names) < 2:
            trivial = {name: {name: 0.0} for name in names}
            return trivial, trivial

        coords_param = ";".join(
            f"{locations[name][1]},{locations[name][0]}" for name in names
        )
        url = f"{self.settings.osrm_base_url.rstrip('/')}/table/v1/driving/{coords_param}"

        try:
            response = requests.get(
                url,
                params={"annotations": "distance,duration"},
                headers={"User-Agent": self.settings.nominatim_user_agent},
                timeout=self.settings.osrm_timeout_seconds,
            )
            if response.status_code != 200:
                logger.warning("OSRM Table API returned HTTP %s", response.status_code)
                return None, None

            data = response.json()
            if data.get("code") != "Ok":
                logger.warning("OSRM Table API error code: %s", data.get("code"))
                return None, None

            raw_distances = data.get("distances")
            raw_durations = data.get("durations")
            if not raw_distances or not raw_durations:
                return None, None

            dist_matrix: Dict[str, Dict[str, float]] = {name: {} for name in names}
            dur_matrix: Dict[str, Dict[str, float]] = {name: {} for name in names}

            for i, src in enumerate(names):
                for j, dst in enumerate(names):
                    if i == j:
                        dist_matrix[src][dst] = 0.0
                        dur_matrix[src][dst] = 0.0
                        continue

                    d_meters = raw_distances[i][j]
                    t_seconds = raw_durations[i][j]

                    if d_meters is None:
                        d_km = self.calculate_haversine_km(locations[src], locations[dst])
                    else:
                        d_km = round(float(d_meters) / 1000.0, 3)

                    if t_seconds is None:
                        t_min = round((d_km / max(fallback_speed_kmh, 1.0)) * 60.0, 2)
                    else:
                        t_min = round(float(t_seconds) / 60.0, 2)

                    dist_matrix[src][dst] = d_km
                    dur_matrix[src][dst] = t_min

            return dist_matrix, dur_matrix
        except Exception as exc:
            logger.warning("OSRM Table API request failed, falling back to Haversine: %s", exc)
            return None, None

    def get_matrices(
        self,
        locations: Dict[str, Tuple[float, float]],
        distance_mode: DistanceMode,
        average_speed_km_per_hour: float = 40.0,
    ) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]], str]:
        """
        Resolve distance matrix (km), duration matrix (min), and actual mode used.
        Falls back gracefully to Haversine if road mode fails.
        """
        if distance_mode == DistanceMode.ROAD:
            road_dist, road_dur = self.fetch_osrm_matrices(
                locations, fallback_speed_kmh=average_speed_km_per_hour
            )
            if road_dist is not None and road_dur is not None:
                return road_dist, road_dur, DistanceMode.ROAD.value

        haversine_dist = self.calculate_haversine_matrix(locations)
        haversine_dur = self.calculate_duration_matrix_from_distances(
            haversine_dist, average_speed_km_per_hour=average_speed_km_per_hour
        )
        return haversine_dist, haversine_dur, DistanceMode.HAVERSINE.value

    @staticmethod
    def get_total_route_distance(
        route: List[str], distance_matrix: Dict[str, Dict[str, float]]
    ) -> float:
        """Compute total distance (km) along an ordered sequence of location names."""
        total = 0.0
        for idx in range(len(route) - 1):
            total += distance_matrix[route[idx]][route[idx + 1]]
        return round(total, 3)
