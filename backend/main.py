"""FastAPI application entrypoint for the Delivery Route Optimization System."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import analytics, geocoding, health, routing
from backend.core.config import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "REST API for geocoding, road/Haversine distance matrices, "
            "Dijkstra / A* / Held-Karp / 2-Opt / Simulated Annealing route optimization, "
            "and logistics analytics."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.api_prefix
    application.include_router(health.router, prefix=prefix)
    application.include_router(geocoding.router, prefix=prefix)
    application.include_router(routing.router, prefix=prefix)
    application.include_router(analytics.router, prefix=prefix)

    @application.get("/", tags=["Root"])
    def root() -> dict:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": f"{prefix}/health",
        }

    return application


app = create_app()
