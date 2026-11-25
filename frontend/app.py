"""
Delivery Route Optimization System — Streamlit Frontend.
Communicates with the FastAPI backend over REST API.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

import streamlit as st

# Ensure repository root is importable regardless of working directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.api_client import BackendAPIClient, BackendAPIError, start_embedded_backend_if_needed
from frontend.components.analytics_panel import (
    render_algorithm_comparison,
    render_breakdown_and_charts,
    render_kpis_and_route_summary,
)
from frontend.components.location_manager import (
    render_delivery_locations_section,
    render_presets_bar,
    render_warehouse_section,
)
from frontend.components.map_viewer import render_route_map
from frontend.components.styles import inject_global_styles, render_header, render_route_flow
from frontend.config import (
    ALGORITHM_OPTIONS,
    BACKEND_URL,
    DEFAULT_VEHICLE_CONFIG,
    DISTANCE_MODE_OPTIONS,
)


@st.cache_resource(show_spinner=False)
def _bootstrap_backend(url: str) -> bool:
    return start_embedded_backend_if_needed(url)


def _init_session_state() -> None:
    defaults = {
        "warehouse_name": "",
        "warehouse_coords": None,
        "warehouse_meta": None,
        "delivery_stops": [],
        "optimization_result": None,
        "comparison_result": None,
        "route_render_id": 0,
        "form_reset_nonce": 0,
        "last_vehicle_config": dict(DEFAULT_VEHICLE_CONFIG),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _build_route_payload(
    algorithm: str,
    distance_mode: str,
    round_trip: bool,
    include_road_geometry: bool,
    vehicle: Dict[str, Any],
) -> Dict[str, Any]:
    wh_lat, wh_lon = st.session_state.warehouse_coords
    return {
        "warehouse": {
            "name": st.session_state.warehouse_name,
            "coordinates": {"lat": wh_lat, "lon": wh_lon},
        },
        "delivery_locations": [
            {
                "name": stop["name"],
                "coordinates": {"lat": stop["lat"], "lon": stop["lon"]},
            }
            for stop in st.session_state.delivery_stops
        ],
        "algorithm": algorithm,
        "distance_mode": distance_mode,
        "round_trip": round_trip,
        "include_road_geometry": include_road_geometry,
        "vehicle": vehicle,
    }


def _render_sidebar(api_client: BackendAPIClient, backend_online: bool) -> Dict[str, Any]:
    with st.sidebar:
        logo_path = PROJECT_ROOT / "assets" / "truck.png"
        if logo_path.exists():
            col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
            with col_img2:
                st.image(str(logo_path), width=110)

        st.header("⚙️ Route & Vehicle Settings")

        if backend_online:
            st.success(f"🟢 FastAPI Online\n`{BACKEND_URL}`")
            st.caption(f"API Docs: {BACKEND_URL}/docs")
        else:
            st.error(f"🔴 FastAPI Offline (`{BACKEND_URL}`)")

        algorithm = st.selectbox(
            "Optimization Algorithm",
            options=list(ALGORITHM_OPTIONS.keys()),
            format_func=lambda k: ALGORITHM_OPTIONS[k],
            index=0,
        )
        distance_mode = st.selectbox(
            "Distance Calculation Mode",
            options=list(DISTANCE_MODE_OPTIONS.keys()),
            format_func=lambda k: DISTANCE_MODE_OPTIONS[k],
            index=0,
        )
        round_trip = st.toggle("🔄 Round Trip (Return to Warehouse)", value=True)
        include_road_geometry = st.toggle("🛣️ Draw Road-Following Polylines", value=True)

        st.markdown("---")
        st.subheader("🚚 Vehicle & Cost Parameters")
        currency_symbol = st.selectbox("Currency", options=["₹", "$", "€", "£"], index=0)
        mileage = st.number_input("Vehicle Mileage (km/L)", min_value=1.0, max_value=100.0, value=15.0, step=0.5)
        fuel_price = st.number_input(f"Fuel Price ({currency_symbol}/L)", min_value=0.0, max_value=1000.0, value=100.0, step=1.0)
        avg_speed = st.number_input("Average Speed (km/h)", min_value=5.0, max_value=150.0, value=40.0, step=5.0)
        stop_time = st.number_input("Service Time per Stop (min)", min_value=0.0, max_value=120.0, value=10.0, step=1.0)

        return {
            "algorithm": algorithm,
            "distance_mode": distance_mode,
            "round_trip": round_trip,
            "include_road_geometry": include_road_geometry,
            "vehicle": {
                "mileage_km_per_liter": float(mileage),
                "average_speed_km_per_hour": float(avg_speed),
                "fuel_price_per_liter": float(fuel_price),
                "stop_time_minutes": float(stop_time),
                "co2_kg_per_liter": 2.31,
                "currency_symbol": currency_symbol,
            },
        }


def main() -> None:
    st.set_page_config(
        page_title="Delivery Route Optimization System",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _init_session_state()
    inject_global_styles()

    backend_online = _bootstrap_backend(BACKEND_URL)
    api_client = BackendAPIClient(BACKEND_URL)

    # Verify health dynamically on render
    if backend_online:
        try:
            api_client.health()
        except BackendAPIError:
            backend_online = False

    settings = _render_sidebar(api_client, backend_online)

    render_header()
    render_presets_bar()
    st.markdown("---")

    render_warehouse_section(api_client)
    st.markdown("---")
    render_delivery_locations_section(api_client)

    st.markdown("---")

    stops = st.session_state.delivery_stops
    ready_stops = [s for s in stops if s["status"] == "ready"]
    can_optimize = (
        backend_online
        and bool(st.session_state.warehouse_name)
        and st.session_state.warehouse_coords is not None
        and len(stops) > 0
        and len(ready_stops) == len(stops)
    )

    if not can_optimize:
        missing = []
        if not backend_online:
            missing.append("Start FastAPI backend server")
        if not st.session_state.warehouse_name or st.session_state.warehouse_coords is None:
            missing.append("Set and geocode a warehouse location")
        if not stops:
            missing.append("Add at least 1 delivery location")
        elif len(ready_stops) < len(stops):
            missing.append(f"Resolve {len(stops) - len(ready_stops)} failed delivery stop(s)")
        st.warning("⚠️ Complete setup before optimizing: " + " · ".join(missing))

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        optimize_clicked = st.button(
            "🚀 Optimize Delivery Route",
            type="primary",
            disabled=not can_optimize,
            width="stretch",
        )
    with btn_col2:
        compare_clicked = st.button(
            "⚡ Compare All Algorithms",
            disabled=not can_optimize,
            width="stretch",
        )

    if optimize_clicked and can_optimize:
        payload = _build_route_payload(**settings)
        with st.spinner("🚀 Optimizing route via FastAPI backend..."):
            try:
                result = api_client.optimize_route(payload)
                st.session_state.optimization_result = result
                st.session_state.last_vehicle_config = settings["vehicle"]
                st.session_state.route_render_id += 1
                st.success("✅ Route optimized successfully!")
            except BackendAPIError as exc:
                st.error(f"❌ Optimization failed: {exc}")

    if compare_clicked and can_optimize:
        compare_payload = {
            "warehouse": {
                "name": st.session_state.warehouse_name,
                "coordinates": {
                    "lat": st.session_state.warehouse_coords[0],
                    "lon": st.session_state.warehouse_coords[1],
                },
            },
            "delivery_locations": [
                {
                    "name": stop["name"],
                    "coordinates": {"lat": stop["lat"], "lon": stop["lon"]},
                }
                for stop in st.session_state.delivery_stops
            ],
            "distance_mode": settings["distance_mode"],
            "round_trip": settings["round_trip"],
            "vehicle": settings["vehicle"],
        }
        with st.spinner("⚡ Benchmarking Dijkstra, A*, 2-Opt, Held-Karp & Simulated Annealing..."):
            try:
                st.session_state.comparison_result = api_client.compare_algorithms(compare_payload)
            except BackendAPIError as exc:
                st.error(f"❌ Comparison failed: {exc}")

    # Live analytics update if user changes vehicle settings after optimizing
    if (
        st.session_state.optimization_result is not None
        and settings["vehicle"] != st.session_state.last_vehicle_config
        and backend_online
    ):
        opt = st.session_state.optimization_result
        try:
            updated_analytics = api_client.recalculate_analytics(
                {
                    "warehouse": opt["warehouse"],
                    "input_delivery_order": [s["name"] for s in st.session_state.delivery_stops],
                    "optimized_route": opt["optimized_route"],
                    "total_distance_km": opt["total_distance_km"],
                    "distance_matrix": opt["distance_matrix"],
                    "duration_matrix": opt.get("duration_matrix"),
                    "round_trip": opt["is_round_trip"],
                    "vehicle": settings["vehicle"],
                }
            )
            opt["analytics"] = updated_analytics
            st.session_state.last_vehicle_config = settings["vehicle"]
        except BackendAPIError:
            pass

    if st.session_state.optimization_result is not None:
        result = st.session_state.optimization_result
        st.markdown("---")
        st.header("🎯 Optimization Results")

        trip_label = "Round Trip Route (Warehouse → Deliveries → Warehouse)" if result["is_round_trip"] else "One-Way Route (Warehouse → Deliveries)"
        st.success(f"🔄 **{trip_label}**")

        render_route_flow(result["optimized_route"])
        render_kpis_and_route_summary(result)

        st.subheader("🗺️ Interactive Route Map")
        render_route_map(result, render_key=f"route_map_{st.session_state.route_render_id}")

        render_breakdown_and_charts(result)

    if st.session_state.comparison_result is not None:
        st.markdown("---")
        render_algorithm_comparison(st.session_state.comparison_result)

    if st.session_state.optimization_result is not None or st.session_state.comparison_result is not None:
        st.markdown("---")
        st.markdown(
            "<p style='text-align:center;color:#64748B;font-style:italic;'>"
            "Have a safe and smooth delivery journey! Every package delivered brings a smile. 🚚</p>",
            unsafe_allow_html=True,
        )
        c_left, c_mid, c_right = st.columns([1, 2, 1])
        with c_mid:
            if st.button("🔄 Start New Route", type="primary", width="stretch"):
                st.session_state.warehouse_name = ""
                st.session_state.warehouse_coords = None
                st.session_state.warehouse_meta = None
                st.session_state.delivery_stops = []
                st.session_state.optimization_result = None
                st.session_state.comparison_result = None
                st.session_state.form_reset_nonce += 1
                st.rerun()


if __name__ == "__main__":
    main()
