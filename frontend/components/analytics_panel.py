"""Delivery analytics dashboard, Plotly charts, algorithm benchmark, and exports."""

from __future__ import annotations

import html
import json
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from frontend.config import ALGORITHM_OPTIONS


def render_kpis_and_route_summary(result: Dict[str, Any]) -> None:
    """Display top-level route KPIs and nearest-to-farthest order."""
    analytics = result["analytics"]
    curr = analytics["currency_symbol"]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("📍 Total Stops", analytics["delivery_count"])
    with c2:
        delta_txt = (
            f"-{analytics['distance_saved_km']:.2f} km saved"
            if analytics["distance_saved_km"] > 0
            else "Optimal baseline"
        )
        st.metric(
            "📏 Total Distance",
            f"{analytics['total_distance_km']:.2f} km",
            delta=delta_txt,
        )
    with c3:
        st.metric(
            "⏱️ Total Time",
            f"{analytics['total_time_hours']:.2f} hrs",
            delta=f"{analytics['travel_time_minutes']:.0f}m drive + {analytics['stop_time_minutes']:.0f}m stops",
            delta_color="off",
        )
    with c4:
        st.metric(
            "⛽ Fuel Needed",
            f"{analytics['fuel_liters']:.2f} L",
            delta=f"-{analytics['fuel_saved_liters']:.2f} L saved" if analytics["fuel_saved_liters"] > 0 else None,
        )
    with c5:
        st.metric(
            f"💰 Fuel Cost ({curr})",
            f"{curr}{analytics['fuel_cost']:.2f}",
            delta=f"-{curr}{analytics['cost_saved']:.2f} saved" if analytics["cost_saved"] > 0 else None,
        )
    with c6:
        st.metric(
            "⭐ Efficiency Score",
            f"{analytics['efficiency_score']}/100",
            delta=f"{analytics['savings_percentage']:.1f}% shorter vs input order",
            delta_color="normal" if analytics["savings_percentage"] > 0 else "off",
        )

    algo_label = ALGORITHM_OPTIONS.get(result["algorithm_used"], result["algorithm_used"])
    st.caption(
        f"Engine: **{algo_label}** · Distance matrix: **{result['distance_mode_used'].upper()}** · "
        f"Solved in **{result['computation_time_ms']:.2f} ms** · "
        f"CO₂ footprint: **{analytics['co2_emissions_kg']:.2f} kg**"
        + (f" ({analytics['co2_saved_kg']:.2f} kg avoided)" if analytics["co2_saved_kg"] > 0 else "")
    )
    if result.get("algorithm_note"):
        st.info(f"ℹ️ {result['algorithm_note']}")

    nearest_order: List[str] = result.get("nearest_order") or []
    if nearest_order:
        st.markdown("**Delivery Order (Nearest → Farthest from Warehouse):**")
        safe_order = " → ".join(html.escape(loc) for loc in nearest_order)
        st.markdown(f'<div class="dro-nearest-banner">{safe_order}</div>', unsafe_allow_html=True)


def render_breakdown_and_charts(result: Dict[str, Any]) -> None:
    """Render leg-by-leg breakdown table, Plotly visualizations, and CSV/JSON downloads."""
    segments: List[Dict[str, Any]] = result["segments"]
    analytics: Dict[str, Any] = result["analytics"]
    curr = analytics["currency_symbol"]

    st.subheader("📋 Leg-by-Leg Route Breakdown")
    rows = []
    for seg in segments:
        rows.append(
            {
                "Leg": str(seg["step"]),
                "From": seg["from_location"],
                "To": seg["to_location"],
                "Type": "Return to Depot" if seg["is_return_leg"] else "Delivery Leg",
                "Distance (km)": f"{seg['distance_km']:.2f}",
                "Cumulative (km)": f"{seg['cumulative_distance_km']:.2f}",
                "Est. Drive (min)": f"{seg['duration_minutes']:.1f}",
                "Geometry": "Road" if seg["is_road_geometry"] else "Direct",
            }
        )
    df_legs = pd.DataFrame(rows)
    st.dataframe(df_legs, width="stretch", hide_index=True)

    # Interactive Plotly Charts
    st.subheader("📊 Delivery Analytics & Optimization Impact")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        df_plot = pd.DataFrame(
            [
                {
                    "Leg": f"Leg {s['step']}: {s['from_location']} → {s['to_location']}",
                    "Distance (km)": s["distance_km"],
                    "Drive Time (min)": s["duration_minutes"],
                    "Type": "Return" if s["is_return_leg"] else "Delivery",
                }
                for s in segments
            ]
        )
        fig_legs = px.bar(
            df_plot,
            x="Leg",
            y="Distance (km)",
            color="Type",
            text="Distance (km)",
            title="Distance per Route Leg",
            color_discrete_map={"Delivery": "#1D4ED8", "Return": "#059669"},
        )
        fig_legs.update_traces(texttemplate="%{text:.2f} km", textposition="outside")
        fig_legs.update_layout(height=360, margin=dict(t=45, b=20, l=20, r=20), xaxis_tickangle=-20)
        st.plotly_chart(fig_legs, width="stretch")

    with chart_col2:
        fig_cmp = go.Figure(
            data=[
                go.Bar(
                    name="Unoptimized Input Order",
                    x=["Distance (km)", "Fuel (L)", f"Fuel Cost ({curr} / 10)"],
                    y=[
                        analytics["baseline_distance_km"],
                        round(analytics["fuel_liters"] + analytics["fuel_saved_liters"], 2),
                        round((analytics["fuel_cost"] + analytics["cost_saved"]) / 10.0, 2),
                    ],
                    marker_color="#94A3B8",
                ),
                go.Bar(
                    name="Optimized Route",
                    x=["Distance (km)", "Fuel (L)", f"Fuel Cost ({curr} / 10)"],
                    y=[
                        analytics["total_distance_km"],
                        analytics["fuel_liters"],
                        round(analytics["fuel_cost"] / 10.0, 2),
                    ],
                    marker_color="#DC2626",
                ),
            ]
        )
        fig_cmp.update_layout(
            barmode="group",
            title="Baseline Input Order vs Optimized Route",
            height=360,
            margin=dict(t=45, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_cmp, width="stretch")

    # Export buttons
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            label="📥 Download Itinerary (CSV)",
            data=df_legs.to_csv(index=False).encode("utf-8"),
            file_name="optimized_route_itinerary.csv",
            mime="text/csv",
            width="stretch",
        )
    with dl2:
        st.download_button(
            label="📥 Download Full Report (JSON)",
            data=json.dumps(result, indent=2).encode("utf-8"),
            file_name="optimized_route_report.json",
            mime="application/json",
            width="stretch",
        )


def render_algorithm_comparison(comparison_result: Dict[str, Any]) -> None:
    """Display side-by-side comparison across routing algorithms."""
    st.subheader("⚡ Multi-Algorithm Benchmark Comparison")
    st.caption(
        f"Baseline (unoptimized input order): **{comparison_result['baseline_distance_km']:.2f} km** · "
        f"Distance Mode: **{comparison_result['distance_mode_used'].upper()}** · "
        f"Winning Algorithm: **{ALGORITHM_OPTIONS.get(comparison_result['best_algorithm'], comparison_result['best_algorithm'])}**"
    )

    items = comparison_result.get("comparisons") or []
    if not items:
        return

    rows = [
        {
            "Algorithm": item["label"],
            "Total Distance (km)": f"{item['total_distance_km']:.2f}",
            "Saved vs Input (km)": f"{item['distance_saved_km']:.2f}",
            "Savings (%)": f"{item['savings_percentage']:.1f}%",
            "Drive Time (min)": f"{item['travel_time_minutes']:.1f}",
            "Fuel Cost": f"{item['fuel_cost']:.2f}",
            "Compute Time (ms)": f"{item['computation_time_ms']:.2f}",
        }
        for item in items
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    df_chart = pd.DataFrame(
        [
            {"Algorithm": "Baseline (Input Order)", "Distance (km)": comparison_result["baseline_distance_km"]},
            *[{"Algorithm": it["label"], "Distance (km)": it["total_distance_km"]} for it in items],
        ]
    )
    fig = px.bar(
        df_chart,
        x="Distance (km)",
        y="Algorithm",
        orientation="h",
        text="Distance (km)",
        title="Total Route Distance by Algorithm (Shorter is Better)",
        color="Distance (km)",
        color_continuous_scale="Teal_r",
    )
    fig.update_traces(texttemplate="%{text:.2f} km", textposition="outside")
    fig.update_layout(height=320, margin=dict(t=45, b=20, l=20, r=40), coloraxis_showscale=False)
    st.plotly_chart(fig, width="stretch")
