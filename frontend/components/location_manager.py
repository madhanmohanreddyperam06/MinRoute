"""Warehouse and delivery stops management UI components."""

from __future__ import annotations

from typing import Dict, List

import pandas as pd
import streamlit as st

from frontend.api_client import BackendAPIClient, BackendAPIError
from frontend.config import SAMPLE_PRESETS


def invalidate_results() -> None:
    """Clear stale route results whenever inputs change."""
    st.session_state.optimization_result = None
    st.session_state.comparison_result = None


def load_sample_preset(preset_name: str) -> None:
    """Populate warehouse and delivery stops from a sample preset."""
    preset = SAMPLE_PRESETS[preset_name]
    wh = preset["warehouse"]
    st.session_state.warehouse_name = wh["name"]
    st.session_state.warehouse_coords = (wh["lat"], wh["lon"])
    st.session_state.warehouse_meta = {
        "display_name": f"{wh['name']} (Sample Preset)",
        "source": "preset",
        "error": None,
    }
    st.session_state.delivery_stops = [
        {
            "name": item["name"],
            "lat": item["lat"],
            "lon": item["lon"],
            "display_name": f"{item['name']} (Sample Preset)",
            "source": "preset",
            "status": "ready",
            "error": None,
        }
        for item in preset["deliveries"]
    ]
    st.session_state.form_reset_nonce += 1
    invalidate_results()


def render_presets_bar() -> None:
    """Render quick-load demo route buttons."""
    st.markdown("**⚡ Quick Demo Presets:**")
    cols = st.columns(len(SAMPLE_PRESETS))
    for col, preset_name in zip(cols, SAMPLE_PRESETS.keys()):
        with col:
            if st.button(f"📌 {preset_name}", width="stretch", key=f"preset_{preset_name}"):
                load_sample_preset(preset_name)
                st.rerun()


def render_warehouse_section(api_client: BackendAPIClient) -> None:
    """Render warehouse input, geocoding, manual coordinate fallback, and status card."""
    st.subheader("🏢 Warehouse (Depot) Location")

    nonce = st.session_state.form_reset_nonce
    with st.form(key=f"warehouse_form_{nonce}", clear_on_submit=False):
        col_in, col_btn = st.columns([4, 1])
        with col_in:
            wh_input = st.text_input(
                "Enter Warehouse Address or 'lat, lon'",
                value=st.session_state.warehouse_name,
                placeholder="e.g., Chennai Central, Mumbai Port, or 13.0824, 80.2759",
                help="Starting depot (and return point for round trips)",
            )
        with col_btn:
            st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("📍 Set Depot", type="primary", width="stretch")

    if submitted:
        cleaned = wh_input.strip()
        if not cleaned:
            st.warning("⚠️ Please enter a warehouse address.")
        elif any(stop["name"].lower() == cleaned.lower() for stop in st.session_state.delivery_stops):
            st.error("❌ Warehouse cannot have the same name as an existing delivery stop.")
        else:
            with st.spinner(f"🔍 Geocoding warehouse '{cleaned}'..."):
                try:
                    geo = api_client.geocode(cleaned)
                    st.session_state.warehouse_name = cleaned
                    invalidate_results()
                    if geo.get("success"):
                        st.session_state.warehouse_coords = (
                            float(geo["latitude"]),
                            float(geo["longitude"]),
                        )
                        st.session_state.warehouse_meta = {
                            "display_name": geo.get("display_name") or cleaned,
                            "source": geo.get("source") or "api",
                            "error": None,
                        }
                        st.success(f"✅ Warehouse set: {cleaned}")
                    else:
                        st.session_state.warehouse_coords = None
                        st.session_state.warehouse_meta = {
                            "display_name": cleaned,
                            "source": None,
                            "error": geo.get("error") or "Geocoding failed",
                        }
                        st.error(f"❌ {st.session_state.warehouse_meta['error']}")
                except BackendAPIError as exc:
                    st.error(f"❌ {exc}")

    # Optional manual coordinate override
    with st.expander("🧭 Enter / Adjust Warehouse Coordinates Manually", expanded=False):
        default_lat = st.session_state.warehouse_coords[0] if st.session_state.warehouse_coords else 13.0824
        default_lon = st.session_state.warehouse_coords[1] if st.session_state.warehouse_coords else 80.2759
        with st.form(key=f"manual_wh_form_{nonce}"):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1:
                m_name = st.text_input("Warehouse Label", value=st.session_state.warehouse_name or "Custom Warehouse")
            with c2:
                m_lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=float(default_lat), format="%.6f")
            with c3:
                m_lon = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=float(default_lon), format="%.6f")
            with c4:
                st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
                apply_manual = st.form_submit_button("Apply", width="stretch")
        if apply_manual:
            label = m_name.strip()
            if not label:
                st.warning("⚠️ Warehouse label cannot be empty.")
            elif any(s["name"].lower() == label.lower() for s in st.session_state.delivery_stops):
                st.error("❌ Label matches an existing delivery stop.")
            else:
                st.session_state.warehouse_name = label
                st.session_state.warehouse_coords = (float(m_lat), float(m_lon))
                st.session_state.warehouse_meta = {
                    "display_name": f"{label} ({m_lat:.4f}, {m_lon:.4f})",
                    "source": "manual",
                    "error": None,
                }
                st.session_state.form_reset_nonce += 1
                invalidate_results()
                st.rerun()

    if st.session_state.warehouse_name and st.session_state.warehouse_coords:
        lat, lon = st.session_state.warehouse_coords
        meta = st.session_state.warehouse_meta or {}
        st.success(
            f"🏢 **{st.session_state.warehouse_name}** — "
            f"`{lat:.5f}, {lon:.5f}` · Source: `{meta.get('source', 'resolved')}`"
        )
    elif st.session_state.warehouse_name:
        meta = st.session_state.warehouse_meta or {}
        st.error(f"❌ Warehouse '{st.session_state.warehouse_name}' is not geocoded: {meta.get('error', 'Retry or enter coordinates manually')}")


def _append_stop_from_geocode(name: str, geo: Dict) -> None:
    if geo.get("success"):
        st.session_state.delivery_stops.append(
            {
                "name": name,
                "lat": float(geo["latitude"]),
                "lon": float(geo["longitude"]),
                "display_name": geo.get("display_name") or name,
                "source": geo.get("source") or "api",
                "status": "ready",
                "error": None,
            }
        )
    else:
        st.session_state.delivery_stops.append(
            {
                "name": name,
                "lat": None,
                "lon": None,
                "display_name": name,
                "source": None,
                "status": "failed",
                "error": geo.get("error") or "Could not geocode address",
            }
        )


def render_delivery_locations_section(api_client: BackendAPIClient) -> None:
    """Render delivery stops adder, bulk import, reordering, retry, and status table."""
    st.subheader("📦 Delivery Locations")

    # Single stop form (clears cleanly on submit)
    with st.form(key="add_stop_form", clear_on_submit=True):
        col_in, col_btn = st.columns([4, 1])
        with col_in:
            new_stop = st.text_input(
                "Add Delivery Stop (Address or 'lat, lon')",
                placeholder="e.g., T Nagar, Chennai  or  13.0418, 80.2337",
            )
        with col_btn:
            st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
            add_clicked = st.form_submit_button("➕ Add Stop", type="primary", width="stretch")

    if add_clicked:
        cleaned = new_stop.strip()
        if not cleaned:
            st.warning("⚠️ Please enter a delivery location.")
        elif st.session_state.warehouse_name and cleaned.lower() == st.session_state.warehouse_name.lower():
            st.warning("⚠️ Delivery location cannot be the same as the warehouse.")
        elif any(s["name"].lower() == cleaned.lower() for s in st.session_state.delivery_stops):
            st.warning(f"⚠️ '{cleaned}' is already in the delivery list.")
        elif len(st.session_state.delivery_stops) >= 50:
            st.warning("⚠️ Maximum 50 delivery locations reached.")
        else:
            with st.spinner(f"🔍 Geocoding '{cleaned}'..."):
                try:
                    geo = api_client.geocode(cleaned)
                    _append_stop_from_geocode(cleaned, geo)
                    invalidate_results()
                    st.rerun()
                except BackendAPIError as exc:
                    st.error(f"❌ {exc}")

    # Bulk stop import
    with st.expander("📋 Bulk Add Multiple Stops (one address per line)", expanded=False):
        with st.form(key="bulk_stops_form", clear_on_submit=True):
            bulk_text = st.text_area(
                "Paste delivery addresses (one per line)",
                placeholder="T Nagar, Chennai\nAdyar, Chennai\nVelachery, Chennai",
                height=110,
            )
            bulk_submit = st.form_submit_button("📥 Geocode & Add All", width="stretch")

        if bulk_submit and bulk_text.strip():
            raw_lines = [line.strip() for line in bulk_text.splitlines() if line.strip()]
            existing = {s["name"].lower() for s in st.session_state.delivery_stops}
            if st.session_state.warehouse_name:
                existing.add(st.session_state.warehouse_name.lower())

            to_add: List[str] = []
            for addr in raw_lines:
                if addr.lower() not in existing:
                    existing.add(addr.lower())
                    to_add.append(addr)

            available_slots = max(0, 50 - len(st.session_state.delivery_stops))
            to_add = to_add[:available_slots]

            if not to_add:
                st.info("ℹ️ All entered stops are already added or match the warehouse.")
            else:
                with st.spinner(f"🔄 Batch geocoding {len(to_add)} locations..."):
                    try:
                        batch_res = api_client.batch_geocode(to_add)
                        for item in batch_res.get("results", []):
                            _append_stop_from_geocode(item["address"], item)
                        invalidate_results()
                        st.rerun()
                    except BackendAPIError as exc:
                        st.error(f"❌ {exc}")

    stops = st.session_state.delivery_stops
    if not stops:
        st.info("📍 No delivery stops added yet. Add stops above or load a quick demo preset.")
        return

    # Summary + Clear All bar
    ready_count = sum(1 for s in stops if s["status"] == "ready")
    total_count = len(stops)

    hdr_col, clear_col = st.columns([4, 1])
    with hdr_col:
        if ready_count == total_count:
            st.success(f"🎯 {ready_count}/{total_count} delivery stops geocoded and ready for optimization!")
        else:
            st.warning(f"📍 {ready_count}/{total_count} stops ready · {total_count - ready_count} failed geocoding (retry or remove)")
    with clear_col:
        if st.button("🗑️ Clear All", width="stretch", help="Remove all delivery stops"):
            st.session_state.delivery_stops = []
            invalidate_results()
            st.rerun()

    # Tabular overview
    table_rows = [
        {
            "#": str(idx + 1),
            "Address": s["name"],
            "Coordinates": f"{s['lat']:.5f}, {s['lon']:.5f}" if s["lat"] is not None else "N/A",
            "Source": s["source"] or "—",
            "Status": "✅ Ready" if s["status"] == "ready" else "❌ Failed",
        }
        for idx, s in enumerate(stops)
    ]
    st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)

    # Interactive per-stop management (reorder / retry / remove)
    with st.expander("🛠️ Manage Individual Stops (Reorder / Retry / Remove)", expanded=ready_count < total_count):
        for idx, stop in enumerate(stops):
            c_name, c_up, c_down, c_retry, c_del = st.columns([4, 0.7, 0.7, 0.9, 0.8])
            with c_name:
                status_icon = "✅" if stop["status"] == "ready" else "❌"
                coord_txt = f"({stop['lat']:.4f}, {stop['lon']:.4f})" if stop["lat"] is not None else f"— {stop.get('error', 'Failed')}"
                st.markdown(f"**{idx + 1}. {stop['name']}** {status_icon} `{coord_txt}`")
            with c_up:
                if st.button("↑", key=f"up_{idx}", disabled=idx == 0, help="Move up", width="stretch"):
                    stops[idx - 1], stops[idx] = stops[idx], stops[idx - 1]
                    invalidate_results()
                    st.rerun()
            with c_down:
                if st.button("↓", key=f"down_{idx}", disabled=idx == len(stops) - 1, help="Move down", width="stretch"):
                    stops[idx + 1], stops[idx] = stops[idx], stops[idx + 1]
                    invalidate_results()
                    st.rerun()
            with c_retry:
                if st.button("↻", key=f"retry_{idx}", disabled=stop["status"] == "ready", help="Retry geocoding", width="stretch"):
                    try:
                        geo = api_client.geocode(stop["name"], use_cache=False)
                        if geo.get("success"):
                            stop.update(
                                {
                                    "lat": float(geo["latitude"]),
                                    "lon": float(geo["longitude"]),
                                    "display_name": geo.get("display_name") or stop["name"],
                                    "source": geo.get("source") or "api",
                                    "status": "ready",
                                    "error": None,
                                }
                            )
                        else:
                            stop["error"] = geo.get("error") or "Retry failed"
                        invalidate_results()
                        st.rerun()
                    except BackendAPIError as exc:
                        st.error(str(exc))
            with c_del:
                if st.button("✕", key=f"del_{idx}", help="Remove stop", width="stretch"):
                    stops.pop(idx)
                    invalidate_results()
                    st.rerun()
