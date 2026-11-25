"""Unified cross-platform launcher for FastAPI backend + Streamlit frontend."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_HOST = os.getenv("DRO_BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = os.getenv("DRO_BACKEND_PORT", "8000")
FRONTEND_PORT = os.getenv("DRO_FRONTEND_PORT", "8501")
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"


def wait_for_backend(timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(f"{BACKEND_URL}/api/v1/health", timeout=1.0)
            if resp.status_code == 200:
                return True
        except httpx.HTTPError:
            time.sleep(0.25)
    return False


def main() -> int:
    env = os.environ.copy()
    env.setdefault("DRO_BACKEND_URL", BACKEND_URL)

    print(f"Starting FastAPI backend at {BACKEND_URL} ...")
    backend_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            BACKEND_HOST,
            "--port",
            str(BACKEND_PORT),
        ],
        cwd=str(ROOT_DIR),
        env=env,
    )

    if not wait_for_backend():
        print("Error: FastAPI backend failed to become healthy.", file=sys.stderr)
        backend_proc.terminate()
        return 1

    print(f"FastAPI ready! Docs available at {BACKEND_URL}/docs")
    print(f"Starting Streamlit frontend at http://localhost:{FRONTEND_PORT} ...")

    frontend_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(ROOT_DIR / "frontend" / "app.py"),
            "--server.port",
            str(FRONTEND_PORT),
        ],
        cwd=str(ROOT_DIR),
        env=env,
    )

    def _shutdown(signum=None, frame=None):
        for proc in (frontend_proc, backend_proc):
            if proc.poll() is None:
                proc.terminate()

    signal.signal(signal.SIGINT, _shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _shutdown)

    try:
        return frontend_proc.wait()
    finally:
        _shutdown()
        for proc in (frontend_proc, backend_proc):
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
