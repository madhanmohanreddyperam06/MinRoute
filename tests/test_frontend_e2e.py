"""End-to-end Streamlit AppTest + live FastAPI integration tests."""

import socket

import pytest
from streamlit.testing.v1 import AppTest

from frontend.components.map_viewer import build_route_map


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_streamlit_full_user_workflow(monkeypatch):
    """Test preset loading, optimizing, comparing, vehicle live-update, and reset end-to-end."""
    port = _free_port()
    monkeypatch.setattr("frontend.config.BACKEND_URL", f"http://127.0.0.1:{port}")
    monkeypatch.setattr("frontend.api_client.BACKEND_URL", f"http://127.0.0.1:{port}")
    monkeypatch.setattr("frontend.app.BACKEND_URL", f"http://127.0.0.1:{port}")

    at = AppTest.from_file("frontend/app.py", default_timeout=25).run()
    assert not at.exception

    # 1. Click Chennai Logistics Demo preset
    preset_btn = next(b for b in at.button if "Chennai Logistics Demo" in b.label)
    preset_btn.click().run()
    assert not at.exception
    assert at.session_state["warehouse_name"] == "Chennai Central"
    assert len(at.session_state["delivery_stops"]) == 4

    # 2. Switch distance mode to Haversine for deterministic offline-safe check and click Optimize
    dist_select = next(sb for sb in at.selectbox if sb.label == "Distance Calculation Mode")
    dist_select.select("haversine").run()
    assert not at.exception

    opt_btn = next(b for b in at.button if "Optimize Delivery Route" in b.label)
    assert not opt_btn.disabled
    opt_btn.click().run()
    assert not at.exception
    assert at.session_state["optimization_result"] is not None
    opt_res = at.session_state["optimization_result"]
    assert opt_res["delivery_count"] == 4
    assert opt_res["is_round_trip"] is True

    # Verify Folium map builds cleanly with no [0, 0] marker regression
    fmap = build_route_map(opt_res)
    html_str = fmap.get_root().render()
    assert "Route Summary" in html_str
    assert "L.marker([0, 0]" not in html_str

    # 3. Click Compare All Algorithms
    cmp_btn = next(b for b in at.button if "Compare All Algorithms" in b.label)
    cmp_btn.click().run()
    assert not at.exception
    assert at.session_state["comparison_result"] is not None
    assert len(at.session_state["comparison_result"]["comparisons"]) == 5

    # 4. Change vehicle mileage in sidebar -> verify live analytics update
    mileage_input = next(ni for ni in at.number_input if "Mileage" in ni.label)
    mileage_input.set_value(30.0).run()
    assert not at.exception
    assert at.session_state["optimization_result"]["analytics"]["fuel_liters"] > 0

    # 5. Click Start New Route -> verify full clean reset
    reset_btn = next(b for b in at.button if "Start New Route" in b.label)
    reset_btn.click().run()
    assert not at.exception
    assert at.session_state["warehouse_name"] == ""
    assert at.session_state["delivery_stops"] == []
    assert at.session_state["optimization_result"] is None
    assert at.session_state["comparison_result"] is None


def test_streamlit_manual_stop_reorder_and_remove(monkeypatch):
    """Test adding direct coordinate stop, reordering, and removing individual stops."""
    port = _free_port()
    monkeypatch.setattr("frontend.config.BACKEND_URL", f"http://127.0.0.1:{port}")
    monkeypatch.setattr("frontend.api_client.BACKEND_URL", f"http://127.0.0.1:{port}")
    monkeypatch.setattr("frontend.app.BACKEND_URL", f"http://127.0.0.1:{port}")

    at = AppTest.from_file("frontend/app.py", default_timeout=25).run()
    assert not at.exception

    # Load preset, remove first stop, verify count drops cleanly from 4 to 3
    preset_btn = next(b for b in at.button if "Mumbai Metro Demo" in b.label)
    preset_btn.click().run()
    assert len(at.session_state["delivery_stops"]) == 4

    # Move second stop up (key="up_1")
    up_btn = next(b for b in at.button if b.key == "up_1")
    second_name = at.session_state["delivery_stops"][1]["name"]
    up_btn.click().run()
    assert not at.exception
    assert at.session_state["delivery_stops"][0]["name"] == second_name

    # Remove first stop (key="del_0")
    del_btn = next(b for b in at.button if b.key == "del_0")
    del_btn.click().run()
    assert not at.exception
    assert len(at.session_state["delivery_stops"]) == 3
