"""Geocoding service with coordinate parsing, Nominatim, Photon backup, and fallback cache."""

from __future__ import annotations

import logging
import re
import threading
import time
from typing import Dict, List, Optional, Tuple

import requests
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim

from backend.core.config import Settings, get_settings
from backend.models.schemas import GeocodeResponse

logger = logging.getLogger(__name__)

# Matches direct latitude/longitude coordinate pairs like "13.0827, 80.2707" or "(13.0827 80.2707)"
_COORDINATE_PATTERN = re.compile(
    r"^\(?\s*([-+]?\d{1,2}(?:\.\d+)?)\s*[,;\s]\s*([-+]?\d{1,3}(?:\.\d+)?)\s*\)?$"
)


class GeocodingService:
    """Thread-safe geocoding service with caching and multi-tier fallbacks."""

    # Fallback reference coordinates for offline resilience and quick demo presets.
    # Only consulted AFTER live geocoding fails (unless offline), using exact or whole-word longest match.
    FALLBACK_COORDINATES: Dict[str, Tuple[float, float]] = {
        "chennai central": (13.0824, 80.2759),
        "chennai port": (13.0846, 80.2844),
        "chennai airport": (12.9844, 80.1745),
        "anna nagar": (13.0850, 80.2101),
        "t nagar": (13.0418, 80.2337),
        "red hills": (13.1667, 80.1833),
        "madhavaram": (13.1429, 80.2325),
        "perambur": (13.1166, 80.2316),
        "puzhal": (13.1345, 80.2033),
        "adyar": (13.0012, 80.2565),
        "velachery": (12.9816, 80.2186),
        "ambattur": (13.0808, 80.2125),
        "tambaram": (12.9249, 80.1000),
        "guindy": (13.0067, 80.2206),
        "mylapore": (13.0368, 80.2676),
        "chennai": (13.0827, 80.2707),
        "mumbai": (19.0760, 72.8777),
        "mumbai port": (18.9532, 72.8482),
        "andheri": (19.1136, 72.8697),
        "bandra": (19.0596, 72.8295),
        "dadar": (19.0178, 72.8478),
        "powai": (19.1176, 72.9060),
        "new delhi": (28.6139, 77.2090),
        "delhi": (28.6139, 77.2090),
        "connaught place": (28.6315, 77.2167),
        "noida": (28.5355, 77.3910),
        "gurugram": (28.4595, 77.0266),
        "bangalore": (12.9716, 77.5946),
        "bengaluru": (12.9716, 77.5946),
        "hyderabad": (17.3850, 78.4867),
        "kolkata": (22.5726, 88.3639),
        "pune": (18.5204, 73.8567),
    }

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._lock = threading.Lock()
        self._last_request_time: float = 0.0
        self._session_cache: Dict[str, GeocodeResponse] = {}
        self._nominatim: Optional[Nominatim] = None

    def _get_nominatim(self) -> Nominatim:
        if self._nominatim is None:
            self._nominatim = Nominatim(
                user_agent=self.settings.nominatim_user_agent,
                timeout=self.settings.nominatim_timeout_seconds,
            )
        return self._nominatim

    @staticmethod
    def parse_direct_coordinates(address: str) -> Optional[Tuple[float, float]]:
        """Parse direct 'lat, lon' coordinate strings if valid."""
        match = _COORDINATE_PATTERN.match(address.strip())
        if not match:
            return None
        lat = float(match.group(1))
        lon = float(match.group(2))
        if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
            return (round(lat, 6), round(lon, 6))
        return None

    @classmethod
    def lookup_fallback_cache(cls, address: str) -> Optional[Tuple[str, Tuple[float, float]]]:
        """
        Look up address in built-in fallback dictionary.

        Matches exact normalized string first, then longest whole-word match.
        Never matches short queries as substrings of longer keys (preventing
        bugs like 'port' matching 'chennai port' or 'chennai' overriding 'chennai airport').
        """
        normalized = " ".join(address.lower().strip().split())
        if not normalized:
            return None

        if normalized in cls.FALLBACK_COORDINATES:
            return normalized, cls.FALLBACK_COORDINATES[normalized]

        # Sort keys longest-first so "chennai airport" is checked before "chennai"
        for key in sorted(cls.FALLBACK_COORDINATES.keys(), key=len, reverse=True):
            pattern = rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])"
            if re.search(pattern, normalized):
                return key, cls.FALLBACK_COORDINATES[key]

        return None

    def _respect_rate_limit(self) -> None:
        """Enforce minimum interval between Nominatim API requests safely across threads."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            wait_seconds = self.settings.nominatim_min_interval_seconds - elapsed
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            self._last_request_time = time.monotonic()

    def _query_nominatim(self, address: str, max_retries: int = 2) -> Optional[GeocodeResponse]:
        """Attempt live geocoding using OpenStreetMap Nominatim."""
        geocoder = self._get_nominatim()
        for attempt in range(max_retries):
            try:
                self._respect_rate_limit()
                location = geocoder.geocode(
                    address,
                    timeout=self.settings.nominatim_timeout_seconds,
                )
                if location is not None:
                    return GeocodeResponse(
                        address=address,
                        success=True,
                        latitude=round(float(location.latitude), 6),
                        longitude=round(float(location.longitude), 6),
                        display_name=str(getattr(location, "address", address)),
                        source="nominatim",
                    )
                return None
            except (GeocoderTimedOut, GeocoderServiceError) as exc:
                logger.warning("Nominatim attempt %d/%d failed for '%s': %s", attempt + 1, max_retries, address, exc)
            except Exception as exc:
                logger.warning("Unexpected Nominatim error for '%s': %s", address, exc)
                break
        return None

    def _query_photon(self, address: str) -> Optional[GeocodeResponse]:
        """Attempt secondary geocoding using Photon (Komoot OSM API)."""
        try:
            response = requests.get(
                self.settings.photon_api_url,
                params={"q": address, "limit": 1},
                headers={"User-Agent": self.settings.nominatim_user_agent},
                timeout=self.settings.nominatim_timeout_seconds,
            )
            if response.status_code != 200:
                return None
            payload = response.json()
            features = payload.get("features") or []
            if not features:
                return None
            coords = features[0].get("geometry", {}).get("coordinates")
            if not coords or len(coords) < 2:
                return None
            lon, lat = float(coords[0]), float(coords[1])
            props = features[0].get("properties", {})
            parts = [props.get("name"), props.get("city"), props.get("state"), props.get("country")]
            display = ", ".join(str(p) for p in parts if p) or address
            return GeocodeResponse(
                address=address,
                success=True,
                latitude=round(lat, 6),
                longitude=round(lon, 6),
                display_name=display,
                source="photon",
            )
        except Exception as exc:
            logger.warning("Photon lookup failed for '%s': %s", address, exc)
            return None

    def geocode_address(self, address: str, use_cache: bool = True) -> GeocodeResponse:
        """
        Geocode an address string into coordinates.

        Resolution order:
        1. Direct coordinate parsing ("lat, lon")
        2. Runtime in-memory cache (exact normalized query)
        3. Live Nominatim API
        4. Live Photon API backup
        5. Verified offline fallback lookup
        """
        cleaned = address.strip() if address else ""
        if not cleaned:
            return GeocodeResponse(
                address=address or "",
                success=False,
                error="Address must not be empty.",
            )

        # 1. Direct coordinates
        direct = self.parse_direct_coordinates(cleaned)
        if direct is not None:
            return GeocodeResponse(
                address=cleaned,
                success=True,
                latitude=direct[0],
                longitude=direct[1],
                display_name=f"Coordinates ({direct[0]:.4f}, {direct[1]:.4f})",
                source="coordinates",
            )

        cache_key = " ".join(cleaned.lower().split())

        # 2. Session cache
        if use_cache:
            with self._lock:
                cached = self._session_cache.get(cache_key)
                if cached is not None:
                    return cached.model_copy(update={"address": cleaned})

        # 3. Live Nominatim
        result = self._query_nominatim(cleaned)

        # 4. Photon fallback if Nominatim failed or returned empty
        if result is None:
            result = self._query_photon(cleaned)

        # 5. Built-in fallback cache (offline resilience)
        if result is None:
            fallback = self.lookup_fallback_cache(cleaned)
            if fallback is not None:
                matched_key, (lat, lon) = fallback
                result = GeocodeResponse(
                    address=cleaned,
                    success=True,
                    latitude=lat,
                    longitude=lon,
                    display_name=f"{cleaned} (Offline match: {matched_key.title()})",
                    source="fallback_cache",
                )

        if result is not None and result.success:
            if use_cache:
                with self._lock:
                    self._session_cache[cache_key] = result
            return result

        return GeocodeResponse(
            address=cleaned,
            success=False,
            error=f"Could not geocode address '{cleaned}'. Try a more specific address or 'lat, lon' coordinates.",
        )

    def batch_geocode(self, addresses: List[str], use_cache: bool = True) -> List[GeocodeResponse]:
        """Geocode a list of addresses sequentially with caching."""
        return [self.geocode_address(addr, use_cache=use_cache) for addr in addresses]
