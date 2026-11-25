"""Interactive Folium map renderer consuming backend route segments."""

from __future__ import annotations

import html
from typing import Any, Dict, List, Tuple

import folium
from branca.element import Element
from streamlit_folium import st_folium


def build_route_map(optimization_result: Dict[str, Any]) -> folium.Map:
    """Construct an interactive Folium map from backend optimization output."""
    coordinates: Dict[str, Tuple[float, float]] = {
        k: (float(v[0]), float(v[1]))
        for k, v in optimization_result["coordinates"].items()
    }
    warehouse: str = optimization_result["warehouse"]
    route: List[str] = optimization_result["optimized_route"]
    segments: List[Dict[str, Any]] = optimization_result["segments"]
    total_distance: float = float(optimization_result["total_distance_km"])
    delivery_count: int = int(optimization_result["delivery_count"])
    algorithm_used: str = optimization_result["algorithm_used"]
    distance_mode_used: str = optimization_result["distance_mode_used"]

    center = coordinates.get(warehouse) or next(iter(coordinates.values()))
    route_map = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap")

    all_bounds_points: List[Tuple[float, float]] = list(coordinates.values())

    # Draw route segments
    for seg in segments:
        geom = [(float(pt[0]), float(pt[1])) for pt in (seg.get("geometry") or [])]
        if len(geom) < 2:
            src_c = coordinates.get(seg["from_location"])
            dst_c = coordinates.get(seg["to_location"])
            if src_c and dst_c:
                geom = [src_c, dst_c]
            else:
                continue

        all_bounds_points.extend(geom)
        is_return = bool(seg.get("is_return_leg", False))
        is_road = bool(seg.get("is_road_geometry", False))

        if is_return:
            color = "#059669"
            leg_label = f"Return Leg {seg['step']}: {seg['from_location']} → {seg['to_location']}"
        else:
            color = "#1D4ED8" if is_road else "#EA580C"
            leg_label = f"Leg {seg['step']}: {seg['from_location']} → {seg['to_location']}"

        dash_array = None if is_road else "8, 6"
        tooltip_txt = (
            f"{leg_label} | {seg['distance_km']:.2f} km "
            f"({seg['duration_minutes']:.1f} min)"
        )

        folium.PolyLine(
            locations=geom,
            color=color,
            weight=4.5,
            opacity=0.88,
            dash_array=dash_array,
            popup=folium.Popup(html.escape(tooltip_txt), max_width=280),
            tooltip=tooltip_txt,
        ).add_to(route_map)

        # Segment midpoint distance badge
        mid_pt = geom[len(geom) // 2]
        badge_html = (
            f'<div style="background:white;padding:2px 6px;border-radius:4px;'
            f'border:1.5px solid {color};font-size:11px;font-weight:700;'
            f'color:{color};white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,0.2);">'
            f'{seg["distance_km"]:.1f} km</div>'
        )
        folium.Marker(
            location=mid_pt,
            icon=folium.DivIcon(html=badge_html, icon_size=(64, 22), icon_anchor=(32, 11)),
        ).add_to(route_map)

    # Add warehouse marker once
    if warehouse in coordinates:
        wh_coords = coordinates[warehouse]
        safe_wh = html.escape(warehouse)
        folium.Marker(
            location=wh_coords,
            popup=folium.Popup(
                f"<b>🏢 {safe_wh}</b><br>Warehouse (Start{' / Return' if optimization_result.get('is_round_trip') else ''})<br>"
                f"<small>{wh_coords[0]:.4f}, {wh_coords[1]:.4f}</small>",
                max_width=260,
            ),
            tooltip=f"🏢 {warehouse} (Warehouse)",
            icon=folium.Icon(color="green", icon="home", prefix="fa"),
        ).add_to(route_map)

    # Add numbered stop markers (single clean numbered DivIcon per delivery stop)
    stop_number = 0
    visited_stops = set()
    for loc in route:
        if loc == warehouse or loc in visited_stops:
            continue
        visited_stops.add(loc)
        stop_number += 1
        coords = coordinates.get(loc)
        if not coords:
            continue
        safe_loc = html.escape(loc)
        folium.Marker(
            location=coords,
            popup=folium.Popup(
                f"<b>📦 Stop #{stop_number}: {safe_loc}</b><br>"
                f"<small>{coords[0]:.4f}, {coords[1]:.4f}</small>",
                max_width=260,
            ),
            tooltip=f"#{stop_number}. {loc}",
            icon=folium.DivIcon(
                html=(
                    f'<div style="background:#1D4ED8;color:#FFFFFF;border-radius:50%;'
                    f'width:28px;height:28px;display:flex;align-items:center;'
                    f'justify-content:center;font-weight:700;font-size:13px;'
                    f'border:2.5px solid #FFFFFF;box-shadow:0 2px 6px rgba(0,0,0,0.35);">'
                    f'{stop_number}</div>'
                ),
                icon_size=(28, 28),
                icon_anchor=(14, 14),
            ),
        ).add_to(route_map)

    # Auto-fit viewport to all route coordinates
    if len(all_bounds_points) >= 2:
        lats = [p[0] for p in all_bounds_points]
        lons = [p[1] for p in all_bounds_points]
        if max(lats) - min(lats) > 1e-4 or max(lons) - min(lons) > 1e-4:
            route_map.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(35, 35))

    # Floating map overlay attached to root HTML (never creates a phantom [0, 0] marker)
    summary_html = f"""
    <div style="
        position: fixed;
        bottom: 18px;
        left: 18px;
        z-index: 9999;
        background: rgba(255, 255, 255, 0.96);
        padding: 10px 14px;
        border-radius: 8px;
        border: 2px solid #1D4ED8;
        box-shadow: 0 4px 12px rgba(0,0,0,0.22);
        font-family: system-ui, -apple-system, sans-serif;
        color: #1E293B;
        min-width: 220px;
    ">
        <div style="font-weight:700;font-size:13px;color:#1E3A8A;margin-bottom:4px;">
            🗺️ Route Summary
        </div>
        <div style="font-size:12px;"><b>Total Distance:</b> {total_distance:.2f} km</div>
        <div style="font-size:12px;"><b>Delivery Stops:</b> {delivery_count}</div>
        <div style="font-size:12px;"><b>Algorithm:</b> {html.escape(algorithm_used)}</div>
        <div style="font-size:12px;"><b>Distance Mode:</b> {html.escape(distance_mode_used.title())}</div>
        <div style="font-size:11px;color:#475569;margin-top:4px;">
            <span style="color:#1D4ED8;">━━</span> Delivery &nbsp;
            <span style="color:#059669;">━━</span> Return &nbsp;
            <span style="color:#EA580C;">┅┅</span> Direct
        </div>
    </div>
    """
    route_map.get_root().html.add_child(Element(summary_html))

    return route_map


def render_route_map(optimization_result: Dict[str, Any], render_key: str) -> None:
    """Build and render the Folium map inside Streamlit without width='100%' errors."""
    route_map = build_route_map(optimization_result)
    st_folium(
        route_map,
        height=560,
        use_container_width=True,
        returned_objects=[],
        key=render_key,
    )
