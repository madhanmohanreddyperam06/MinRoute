"""Road network polyline geometry service using OSRM with thread-safe LRU caching."""

from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from typing import List, Optional, Tuple

import requests

from backend.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class RoadRoutingService:
    """Fetch and cache road-following route geometries between coordinate pairs."""

    def __init__(
        self, settings: Optional[Settings] = None, max_cache_size: int = 500
    ) -> None:
        self.settings = settings or get_settings()
        self._max_cache_size = max_cache_size
        self._cache: OrderedDict[
            Tuple[float, float, float, float], Tuple[List[Tuple[float, float]], bool]
        ] = OrderedDict()
        self._lock = threading.Lock()

    @staticmethod
    def _cache_key(
        start_coords: Tuple[float, float], end_coords: Tuple[float, float]
    ) -> Tuple[float, float, float, float]:
        return (
            round(start_coords[0], 5),
            round(start_coords[1], 5),
            round(end_coords[0], 5),
            round(end_coords[1], 5),
        )

    def _put_cache(
        self,
        start_coords: Tuple[float, float],
        end_coords: Tuple[float, float],
        points: List[Tuple[float, float]],
    ) -> None:
        key = self._cache_key(start_coords, end_coords)
        with self._lock:
            self._cache[key] = (points, True)
            self._cache.move_to_end(key)
            if len(self._cache) > self._max_cache_size:
                self._cache.popitem(last=False)

    def _get_cache(
        self, start_coords: Tuple[float, float], end_coords: Tuple[float, float]
    ) -> Optional[Tuple[List[Tuple[float, float]], bool]]:
        key = self._cache_key(start_coords, end_coords)
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                self._cache.move_to_end(key)
            return cached

    def get_route_geometry(
        self,
        start_coords: Tuple[float, float],
        end_coords: Tuple[float, float],
        use_road_network: bool = True,
    ) -> Tuple[List[Tuple[float, float]], bool]:
        """
        Return (polyline_points, is_road_geometry) where points are (lat, lon).
        Uses OSRM /route/v1/driving/{lon1},{lat1};{lon2},{lat2} with GeoJSON output.
        Falls back cleanly to straight line [start_coords, end_coords] when offline or disabled.
        """
        if start_coords == end_coords:
            return [start_coords, end_coords], True

        if not use_road_network:
            return [start_coords, end_coords], False

        cached = self._get_cache(start_coords, end_coords)
        if cached is not None:
            return cached

        geometry, is_road = self._fetch_osrm_geometry(start_coords, end_coords)
        if is_road:
            self._put_cache(start_coords, end_coords, geometry)
        return geometry, is_road

    def get_multi_leg_geometries(
        self,
        waypoints: List[Tuple[float, float]],
        use_road_network: bool = True,
    ) -> List[Tuple[List[Tuple[float, float]], bool]]:
        """
        Fetch road geometries for all consecutive waypoint pairs in a SINGLE OSRM request
        (with per-leg cache lookup first and graceful straight-line fallback).
        """
        if len(waypoints) < 2:
            return []

        leg_pairs = [(waypoints[i], waypoints[i + 1]) for i in range(len(waypoints) - 1)]

        if not use_road_network:
            return [([src, dst], False) for src, dst in leg_pairs]

        # Serve entirely from cache if every leg is already cached
        cached_results: List[Optional[Tuple[List[Tuple[float, float]], bool]]] = []
        all_cached = True
        for src, dst in leg_pairs:
            if src == dst:
                cached_results.append(([src, dst], True))
            else:
                hit = self._get_cache(src, dst)
                cached_results.append(hit)
                if hit is None:
                    all_cached = False

        if all_cached:
            return [item for item in cached_results if item is not None]

        # Single OSRM request for all legs using steps=true & geometries=geojson
        coords_param = ";".join(f"{pt[1]},{pt[0]}" for pt in waypoints)
        url = f"{self.settings.osrm_base_url.rstrip('/')}/route/v1/driving/{coords_param}"

        try:
            response = requests.get(
                url,
                params={"overview": "false", "geometries": "geojson", "steps": "true"},
                headers={"User-Agent": self.settings.nominatim_user_agent},
                timeout=self.settings.osrm_timeout_seconds,
            )
            if response.status_code == 200:
                data = response.json()
                routes = data.get("routes") or []
                if data.get("code") == "Ok" and routes:
                    legs = routes[0].get("legs") or []
                    if len(legs) == len(leg_pairs):
                        output: List[Tuple[List[Tuple[float, float]], bool]] = []
                        for (src, dst), leg in zip(leg_pairs, legs):
                            leg_points: List[Tuple[float, float]] = []
                            for step in leg.get("steps") or []:
                                coords = step.get("geometry", {}).get("coordinates") or []
                                for pt in coords:
                                    latlon = (round(float(pt[1]), 6), round(float(pt[0]), 6))
                                    if not leg_points or leg_points[-1] != latlon:
                                        leg_points.append(latlon)
                            if len(leg_points) >= 2:
                                self._put_cache(src, dst, leg_points)
                                output.append((leg_points, True))
                            else:
                                output.append(([src, dst], False))
                        return output
        except Exception as exc:
            logger.warning("Multi-leg OSRM geometry request failed: %s", exc)

        # Fallback: preserve any cached legs, straight-line for uncached ones
        fallback: List[Tuple[List[Tuple[float, float]], bool]] = []
        for (src, dst), cached_item in zip(leg_pairs, cached_results):
            if cached_item is not None:
                fallback.append(cached_item)
            else:
                fallback.append(([src, dst], False))
        return fallback

    def _fetch_osrm_geometry(
        self,
        start_coords: Tuple[float, float],
        end_coords: Tuple[float, float],
    ) -> Tuple[List[Tuple[float, float]], bool]:
        url = (
            f"{self.settings.osrm_base_url.rstrip('/')}/route/v1/driving/"
            f"{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}"
        )
        try:
            response = requests.get(
                url,
                params={"overview": "full", "geometries": "geojson"},
                headers={"User-Agent": self.settings.nominatim_user_agent},
                timeout=self.settings.osrm_timeout_seconds,
            )
            if response.status_code != 200:
                logger.warning("OSRM route API HTTP %s", response.status_code)
                return [start_coords, end_coords], False

            data = response.json()
            routes = data.get("routes") or []
            if data.get("code") != "Ok" or not routes:
                return [start_coords, end_coords], False

            raw_coords = routes[0].get("geometry", {}).get("coordinates") or []
            if len(raw_coords) < 2:
                return [start_coords, end_coords], False

            points = [(round(float(pt[1]), 6), round(float(pt[0]), 6)) for pt in raw_coords]
            return points, True
        except Exception as exc:
            logger.warning("OSRM geometry fetch failed: %s", exc)
            return [start_coords, end_coords], False
