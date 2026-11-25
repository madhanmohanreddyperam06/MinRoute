"""CSS styles and header component (preserving Streamlit Material icon fonts)."""

from __future__ import annotations

import html
import streamlit as st


def inject_global_styles() -> None:
    """Inject clean responsive CSS without overriding Streamlit's Material icon fonts."""
    st.markdown(
        """
        <style>
        .dro-hero {
            background: linear-gradient(135deg, #E53E3E 0%, #C53030 55%, #9B2C2C 100%);
            padding: 1.5rem 1.75rem;
            border-radius: 14px;
            margin-bottom: 1.25rem;
            text-align: center;
            box-shadow: 0 10px 25px rgba(229, 62, 62, 0.25);
            color: #FFFFFF;
        }
        .dro-hero h1 {
            margin: 0;
            font-size: 2.05rem;
            font-weight: 700;
            letter-spacing: 0.4px;
            color: #FFFFFF;
        }
        .dro-hero p {
            margin: 0.45rem 0 0 0;
            font-size: 1.02rem;
            color: rgba(255, 255, 255, 0.92);
        }
        .dro-workflow-bar {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            gap: 0.65rem;
            padding: 0.75rem 1rem;
            border-radius: 10px;
            background: rgba(128, 128, 128, 0.08);
            border: 1px solid rgba(128, 128, 128, 0.18);
            margin-bottom: 1.2rem;
            font-size: 0.95rem;
            font-weight: 500;
        }
        .dro-route-flow {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: center;
            gap: 0.6rem;
            margin: 1rem 0 1.4rem 0;
        }
        .dro-node-wh {
            background: linear-gradient(135deg, #DC2626, #B91C1C);
            color: #FFFFFF;
            padding: 0.55rem 0.95rem;
            border-radius: 10px;
            font-weight: 700;
            font-size: 0.95rem;
            box-shadow: 0 3px 10px rgba(220, 38, 38, 0.25);
        }
        .dro-node-stop {
            background: #1E293B;
            color: #F8FAFC;
            padding: 0.55rem 0.95rem;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.92rem;
            border: 1px solid #334155;
            box-shadow: 0 3px 8px rgba(15, 23, 42, 0.2);
        }
        .dro-arrow {
            font-size: 1.25rem;
            font-weight: 700;
            color: #64748B;
        }
        .dro-nearest-banner {
            background: rgba(33, 150, 243, 0.1);
            border-left: 4px solid #2196F3;
            padding: 0.75rem 1rem;
            border-radius: 0 8px 8px 0;
            font-weight: 600;
            margin: 0.75rem 0 1.25rem 0;
        }
        @media (max-width: 768px) {
            .dro-hero h1 { font-size: 1.5rem; }
            .dro-hero p { font-size: 0.92rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Render the top banner and workflow steps."""
    st.markdown(
        """
        <div class="dro-hero">
            <h1>🚚 Delivery Route Optimizer</h1>
            <p>FastAPI + Dijkstra, Held-Karp Exact TSP, A*, 2-Opt &amp; Real OSRM Road Routing</p>
        </div>
        <div class="dro-workflow-bar">
            <span>🏢 1. Set Warehouse</span>
            <span>→</span>
            <span>📍 2. Add Delivery Stops</span>
            <span>→</span>
            <span>⚙️ 3. Pick Algorithm &amp; Vehicle</span>
            <span>→</span>
            <span>🚀 4. Optimize &amp; Compare</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_route_flow(route: list[str]) -> None:
    """Render HTML flow diagram for the optimized route sequence."""
    chips = []
    last_idx = len(route) - 1
    stop_num = 0
    for idx, location in enumerate(route):
        safe_loc = html.escape(location)
        if idx == 0 or (idx == last_idx and location == route[0]):
            label = "Start" if idx == 0 else "Return"
            chips.append(f'<div class="dro-node-wh">🏢 {safe_loc} <small>({label})</small></div>')
        else:
            stop_num += 1
            chips.append(f'<div class="dro-node-stop">#{stop_num} 📦 {safe_loc}</div>')
        if idx < last_idx:
            chips.append('<span class="dro-arrow">→</span>')

    st.markdown(f'<div class="dro-route-flow">{"".join(chips)}</div>', unsafe_allow_html=True)
