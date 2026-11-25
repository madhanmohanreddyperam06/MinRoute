"""HTTP client for communicating with the FastAPI backend (with local auto-start option)."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
import uvicorn

from frontend.config import BACKEND_URL


class BackendAPIError(RuntimeError):
    """Raised when the FastAPI backend returns an error or cannot be reached."""


def _is_local_backend(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.hostname in {"127.0.0.1", "localhost", "0.0.0.0"}


def start_embedded_backend_if_needed(backend_url: str = BACKEND_URL) -> bool:
    """
    Ensure FastAPI backend is reachable.
    If configured to localhost and not yet running, spin up an embedded Uvicorn
    server in a daemon thread so `streamlit run frontend/app.py` works out of the box.
    """
    try:
        resp = httpx.get(f"{backend_url}/api/v1/health", timeout=1.2)
        if resp.status_code == 200:
            return True
    except httpx.HTTPError:
        pass

    if not _is_local_backend(backend_url):
        return False

    parsed = urlparse(backend_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8000

    from backend.main import app as fastapi_app

    config = uvicorn.Config(
        fastapi_app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True, name="embedded-fastapi")
    thread.start()

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(f"{backend_url}/api/v1/health", timeout=0.8)
            if resp.status_code == 200:
                return True
        except httpx.HTTPError:
            time.sleep(0.15)
    return False


class BackendAPIClient:
    """Synchronous HTTP client wrapping FastAPI route optimization endpoints."""

    def __init__(self, base_url: str = BACKEND_URL, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/api/v1"
        self.timeout = timeout

    def _request(
        self, method: str, path: str, json_payload: Optional[Dict[str, Any]] = None
    ) -> Any:
        url = f"{self.api_base}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, json=json_payload)
        except httpx.HTTPError as exc:
            raise BackendAPIError(
                f"Cannot reach FastAPI backend at {self.base_url}: {exc}"
            ) from exc

        if response.status_code >= 400:
            detail = response.text
            try:
                err_json = response.json()
                detail = err_json.get("detail", detail)
            except ValueError:
                pass
            raise BackendAPIError(f"API Error ({response.status_code}): {detail}")

        return response.json()

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    def list_algorithms(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/algorithms")

    def geocode(self, address: str, use_cache: bool = True) -> Dict[str, Any]:
        return self._request(
            "POST", "/geocode", {"address": address, "use_cache": use_cache}
        )

    def batch_geocode(
        self, addresses: List[str], use_cache: bool = True
    ) -> Dict[str, Any]:
        return self._request(
            "POST", "/geocode/batch", {"addresses": addresses, "use_cache": use_cache}
        )

    def optimize_route(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/optimize", payload)

    def compare_algorithms(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/compare", payload)

    def recalculate_analytics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/analytics", payload)
