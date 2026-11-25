# Logistics Delivery Route Optimizer
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic)
![Folium](https://img.shields.io/badge/Folium-0.16+-77B829?style=flat-square&logo=leaflet)
![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?style=flat-square&logo=plotly)
![OSRM](https://img.shields.io/badge/Routing-OSRM%20%26%20Haversine-2B6CB0?style=flat-square)
![Algorithms](https://img.shields.io/badge/Algorithms-Dijkstra%20%7C%20A*%20%7C%20Held--Karp%20%7C%202--Opt%20%7C%20SA-orange?style=flat-square)
![Pytest](https://img.shields.io/badge/Pytest-8.x-0A9EDC?style=flat-square&logo=pytest)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

A full-stack logistics route planner powered by a **FastAPI** backend and a **Streamlit** frontend. It combines **Dijkstra's Shortest Path Algorithm**, **Held-Karp Exact Dynamic Programming**, **A\* Search**, **2-Opt Local Search**, and **Simulated Annealing** with real-world **OSRM road network routing** (plus Haversine fallback) to compute optimal delivery routes, interactive maps, and actionable fleet analytics.

## Features

- **Structured Client-Server Architecture**: Clean separation between the FastAPI REST API (`backend/`) and the interactive Streamlit dashboard (`frontend/`).
- **Multi-Algorithm Route Optimization**:
  - **Auto (Best Strategy)**: Automatically selects exact **Held-Karp Dynamic Programming** for up to 11 stops and switches to **2-Opt / Simulated Annealing** for larger routes.
  - **Held-Karp Exact TSP**: Guarantees the mathematically optimal route (up to 14 stops).
  - **Dijkstra + Nearest Neighbor + 2-Opt**: Eliminates path crossings over Dijkstra shortest-path matrices.
  - **Dijkstra + Nearest Neighbor (Classic)**: Classic greedy shortest-path baseline.
  - **A\* Shortest Path + 2-Opt**: Admissible Haversine heuristic search refined with 2-Opt.
  - **Simulated Annealing**: Seeded stochastic search with 2-Opt and stop-relocation moves.
- **Multi-Algorithm Benchmark**: Compare every algorithm side-by-side against your unoptimized input order.
- **Real Road Network & Haversine Distances**: Fetches real driving distances, durations, and road polylines from OSRM (with automatic Haversine fallback when offline).
- **Smart Geocoding**: Supports direct `"lat, lon"` coordinates, live OpenStreetMap Nominatim + Photon fallback, thread-safe rate limiting, in-memory caching, and offline demo fallback.
- **Interactive Map & Analytics**: Numbered Folium route maps with auto-fitted bounds, Plotly visualizations, real savings vs. baseline input order, CO₂ footprint tracking, live vehicle parameter recalculation, and CSV/JSON exports.

## Project Structure

```text
Delivery-Route-Optimizer/
├── backend/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entrypoint & CORS setup
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                # Pydantic settings (API, OSRM, Nominatim, limits)
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py               # Pydantic v2 request/response schemas & validators
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py          # Shared backend service providers
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py            # GET  /api/v1/health
│   │       ├── geocoding.py         # POST /api/v1/geocode & /api/v1/geocode/batch
│   │       ├── routing.py           # GET  /api/v1/algorithms, POST /optimize, /compare
│   │       └── analytics.py         # POST /api/v1/analytics
│   └── services/
│       ├── __init__.py
│       ├── geocoding_service.py     # Coordinate parser, Nominatim, Photon, fallback cache
│       ├── distance_service.py      # OSRM Table API road matrix & Haversine matrix
│       ├── graph_builder.py         # Directed/undirected weighted Graph builder
│       ├── optimizer_service.py     # Dijkstra, A*, 2-Opt, Held-Karp, Simulated Annealing
│       ├── road_routing_service.py  # OSRM road polyline geometry & LRU cache
│       └── analytics_service.py     # Real baseline comparison, fuel, time, CO2, scoring
├── frontend/
│   ├── __init__.py
│   ├── app.py                       # Main Streamlit application
│   ├── config.py                    # Backend URL, algorithm labels, sample presets
│   ├── api_client.py                # HTTPX API client & local embedded backend bootstrap
│   └── components/
│       ├── __init__.py
│       ├── styles.py                # Responsive UI styles & route flow visualization
│       ├── location_manager.py      # Presets, depot/stop forms, bulk import, reordering
│       ├── map_viewer.py            # Folium interactive map with road polylines & overlay
│       └── analytics_panel.py       # KPIs, Plotly charts, benchmark table, CSV/JSON export
├── tests/
│   ├── __init__.py
│   ├── test_distance_and_graph.py   # Haversine & directed graph unit tests
│   ├── test_algorithms.py           # Dijkstra, A*, Held-Karp, 2-Opt & SA tests
│   ├── test_geocoding.py            # Geocoding & cache matching regression tests
│   ├── test_analytics.py            # Baseline comparison & vehicle KPI tests
│   ├── test_road_routing.py         # OSRM polyline & fallback tests
│   └── test_api.py                  # FastAPI TestClient end-to-end endpoint tests
├── assets/
│   └── truck.png                    # Application truck icon
├── .streamlit/
│   └── config.toml                  # Streamlit runtime settings
├── run_app.py                       # Unified launcher for FastAPI + Streamlit
├── requirements.txt                 # Python dependencies
├── LICENSE                          # MIT License
└── README.md                        # Project documentation
```

## Quick Start

### Prerequisites

- Python 3.10 or higher
- `pip` package manager

### Installation

1. **Clone or download the repository**
2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

#### Option 1: Launch Both Backend & Frontend Together (Recommended)

```bash
python run_app.py
```

- **Streamlit UI**: `http://localhost:8501`
- **FastAPI Backend**: `http://127.0.0.1:8000`
- **Interactive API Docs (Swagger)**: `http://127.0.0.1:8000/docs`

#### Option 2: Run Services Separately

1. Start the FastAPI backend:

   ```bash
   uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. In another terminal, start the Streamlit frontend:

   ```bash
   streamlit run frontend/app.py
   ```

> **Note**: If you launch `streamlit run frontend/app.py` on its own without starting Uvicorn first, the frontend automatically bootstraps a local FastAPI backend in the background so everything works out of the box.

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service status, version, and algorithm list |
| `GET` | `/api/v1/algorithms` | Detailed metadata for all routing algorithms |
| `POST` | `/api/v1/geocode` | Geocode a single address or `"lat, lon"` string |
| `POST` | `/api/v1/geocode/batch` | Batch geocode up to 50 addresses |
| `POST` | `/api/v1/optimize` | Optimize delivery route + road geometry + analytics |
| `POST` | `/api/v1/compare` | Benchmark all routing algorithms on the same stops |
| `POST` | `/api/v1/analytics` | Recalculate fuel, time, CO₂, and savings metrics |

## Running Tests

```bash
pytest -v
```

## Algorithm Details

### 1. Dijkstra's Shortest Path + Tour Solvers

- **Dijkstra's Algorithm** computes exact shortest paths in $O((V + E) \log V)$ using a priority queue (`heapq`) over weighted directed/undirected graphs, preserving real-world road asymmetries.
- **Held-Karp Exact TSP** solves the Traveling Salesperson Problem to proven optimality in $O(n^2 \cdot 2^n)$ via bitmask dynamic programming for up to 14 stops.
- **2-Opt & Simulated Annealing** refine tours beyond greedy Nearest Neighbor to eliminate route crossings and scale smoothly up to 50 delivery stops.
- **A\* Search** leverages an admissible great-circle Haversine heuristic $h(n, \text{goal})$ for goal-directed shortest-path lookup.

### 2. Distance Calculation

- **Road Network Mode**: Uses the OSRM Table & Route APIs for true driving distances, durations, and street-level polylines.
- **Haversine Formula** (exact mode & offline fallback):

```text
a = sin²(Δφ/2) + cos φ₁ ⋅ cos φ₂ ⋅ sin²(Δλ/2)
c = 2 ⋅ asin( √min(1, a) )
d = R ⋅ c   (where R = 6371.0 km)
```

## Contact Information

### Madhan Mohan Reddy
- **Mobile**: +91 9110395993

---

**Optimizing deliveries, one route at a time!**
