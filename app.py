"""
AtmosCast: Weather-Aware Air Pollution Forecasting System
Streamlit Dashboard Shell (Phase 1)

Delhi NCR Focus (SIH Problem Statement SIH26082)
"""

import sys
from pathlib import Path
import streamlit as st

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.utils.config import load_config, get_stations, get_pollutants, get_forecast_horizons

# Page configuration
st.set_page_config(
    page_title="AtmosCast | Air Pollution Forecasting System",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Deep navy, Teal accents, light neutral background, rounded cards)
CUSTOM_CSS = """
<style>
    /* Global Styles */
    :root {
        --primary-navy: #0F172A;
        --secondary-teal: #0D9488;
        --accent-teal: #14B8A6;
        --bg-neutral: #F8FAFC;
        --text-slate: #1E293B;
        --muted-slate: #64748B;
        --border-slate: #E2E8F0;
    }

    .main {
        background-color: var(--bg-neutral);
        color: var(--text-slate);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Top banner */
    .hero-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 60%, #0D9488 100%);
        border-radius: 14px;
        padding: 1.75rem 2rem;
        color: #FFFFFF;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
        color: #FFFFFF;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #94A3B8;
        margin: 0.4rem 0 0;
        line-height: 1.4;
    }

    /* Card styling */
    .atmos-card {
        background: #FFFFFF;
        border: 1px solid var(--border-slate);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        margin-bottom: 1rem;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .atmos-card:hover {
        box-shadow: 0 4px 8px -2px rgba(0, 0, 0, 0.08);
        border-color: #CBD5E1;
    }

    /* Status badge/pill */
    .status-pill {
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .status-pill.completed {
        background-color: #ECFDF5;
        color: #059669;
        border: 1px solid #A7F3D0;
    }
    .status-pill.pending {
        background-color: #F8FAFC;
        color: #64748B;
        border: 1px solid #E2E8F0;
    }
    .status-pill.active {
        background-color: #F0FDFA;
        color: #0D9488;
        border: 1px solid #99F6E4;
    }

    /* Station badge */
    .station-badge {
        background: #F1F5F9;
        color: #334155;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 0.25rem 0.55rem;
        border-radius: 6px;
    }

    /* Empty state box */
    .empty-state {
        border: 2px dashed #CBD5E1;
        border-radius: 12px;
        background: #F8FAFC;
        padding: 2rem 1.5rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data
def get_cached_config():
    """Load configuration safely with caching."""
    return load_config()


def render_sidebar(config):
    """Render consistent sidebar navigation and system information."""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding-bottom: 0.75rem; border-bottom: 1px solid #E2E8F0;">
                <h2 style="color: #0F172A; margin: 0; font-weight: 800; font-size: 1.35rem; display: flex; align-items: center; gap: 0.5rem;">
                    🌫️ AtmosCast
                </h2>
                <p style="color: #64748B; font-size: 0.8rem; margin: 0.3rem 0 0 0; line-height: 1.35;">
                    Weather-Aware Air Pollution Forecasting<br>
                    <span style="color: #0D9488; font-weight: 600;">SIH26082 • Delhi NCR Focus</span>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Navigation")
        pages = [
            "1. Overview",
            "2. Live & Historical Air Quality",
            "3. 72-Hour Forecast",
            "4. Weather Analysis",
            "5. Pollution Episode Analysis",
            "6. Model Performance",
            "7. Explainable AI",
            "8. Data Sources & Project Information",
        ]
        selected_page = st.radio("Go to view:", pages, index=0, label_visibility="collapsed")

        st.markdown("---")
        st.markdown("### Selected Monitoring Station")
        stations = get_stations(config)
        selected_station_name = st.selectbox(
            "Select Station",
            options=[s["name"] for s in stations],
            index=0,
            label_visibility="collapsed",
        )
        selected_station = next((s for s in stations if s["name"] == selected_station_name), stations[0])

        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.75rem; margin-top: 0.5rem; font-size: 0.8rem;">
                <div style="font-weight: 600; color: #0F172A;">{selected_station['name']}</div>
                <div style="color: #64748B;">{selected_station['authority']} • {selected_station['city']}</div>
                <div style="color: #0D9488; margin-top: 0.25rem;">
                    {selected_station['latitude']:.4f}°N, {selected_station['longitude']:.4f}°E
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            """
            <div style="font-size: 0.78rem; color: #64748B; line-height: 1.5;">
                <strong>Phase:</strong> 01 (Workspace Initialized)<br>
                <strong>Architecture:</strong> Coupled ML & Meteorology<br>
                <strong>Horizon:</strong> 24h • 48h • 72h
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_page, selected_station


def view_overview(config, station):
    """Render Overview dashboard page."""
    # Hero Header Banner
    st.markdown(
        """
        <div class="hero-header">
            <div class="hero-title">AtmosCast Environmental Intelligence</div>
            <div class="hero-subtitle">
                Coupled air pollution and boundary-layer meteorological forecasting for the Delhi National Capital Region.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Empty-State Architectural KPI Cards
    st.markdown("### Core Forecasting Architecture")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            """
            <div class="atmos-card">
                <div>
                    <span class="status-pill completed">Configured</span>
                    <h4 style="margin: 0.6rem 0 0.2rem; color: #0F172A; font-size: 1rem;">Target Pollutants</h4>
                    <p style="font-size: 1.4rem; font-weight: 800; color: #0D9488; margin: 0;">PM2.5, PM10</p>
                </div>
                <p style="font-size: 0.8rem; color: #64748B; margin: 0.5rem 0 0;">O3, NO2, SO2, CO configured</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="atmos-card">
                <div>
                    <span class="status-pill completed">Configured</span>
                    <h4 style="margin: 0.6rem 0 0.2rem; color: #0F172A; font-size: 1rem;">Forecast Horizons</h4>
                    <p style="font-size: 1.4rem; font-weight: 800; color: #0F172A; margin: 0;">24, 48, 72 hrs</p>
                </div>
                <p style="font-size: 0.8rem; color: #64748B; margin: 0.5rem 0 0;">Multi-step chronological models</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="atmos-card">
                <div>
                    <span class="status-pill completed">Configured</span>
                    <h4 style="margin: 0.6rem 0 0.2rem; color: #0F172A; font-size: 1rem;">Atmospheric Physics</h4>
                    <p style="font-size: 1.4rem; font-weight: 800; color: #0F172A; margin: 0;">PBL & Inversion</p>
                </div>
                <p style="font-size: 0.8rem; color: #64748B; margin: 0.5rem 0 0;">Ventilation coefficient & wind</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            """
            <div class="atmos-card">
                <div>
                    <span class="status-pill active">Phase 1 Complete</span>
                    <h4 style="margin: 0.6rem 0 0.2rem; color: #0F172A; font-size: 1rem;">Data Ingestion Feed</h4>
                    <p style="font-size: 1.4rem; font-weight: 800; color: #64748B; margin: 0;">Standby</p>
                </div>
                <p style="font-size: 0.8rem; color: #64748B; margin: 0.5rem 0 0;">Awaiting Phase 2 ingestion</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Monitored Station Network
    st.markdown("### Delhi NCR Ground Monitoring Stations")
    stations = get_stations(config)
    cols = st.columns(3)
    for idx, st_item in enumerate(stations):
        col = cols[idx % 3]
        with col:
            st.markdown(
                f"""
                <div class="atmos-card" style="margin-bottom: 0.75rem;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 0.95rem; font-weight: 700; color: #0F172A;">{st_item['name']}</span>
                            <span class="station-badge">{st_item['authority']}</span>
                        </div>
                        <p style="font-size: 0.82rem; color: #64748B; margin: 0.4rem 0 0.6rem 0; line-height: 1.35;">
                            {st_item['description']}
                        </p>
                    </div>
                    <div style="font-size: 0.78rem; color: #0D9488; font-weight: 500;">
                        📍 {st_item['latitude']:.4f}°N, {st_item['longitude']:.4f}°E ({st_item['city']})
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Development Progress Section
    st.markdown("### Development Roadmap & Status")
    st.caption("Strictly phased implementation tracking per project governance instructions.")

    phases = [
        ("Phase 01", "Project Initialization & Architecture Setup", "COMPLETED"),
        ("Phase 02", "Multi-Agency Data Ingestion & API Pipelines", "PENDING"),
        ("Phase 03", "Data Harmonization, Time-Series Alignment & Quality Control", "PENDING"),
        ("Phase 04", "Boundary-Layer Meteorology & Atmospheric Feature Engineering", "PENDING"),
        ("Phase 05", "Exploratory Data Analysis & Airshed Episodic Profiling", "PENDING"),
        ("Phase 06", "Baseline Forecasting Models & ML Architecture Setup", "PENDING"),
        ("Phase 07", "Gradient-Boosted Multi-Horizon Forecasting Engine (24h, 48h, 72h)", "PENDING"),
        ("Phase 08", "Rigorous Horizon-Wise & Seasonal Validation Benchmarking", "PENDING"),
        ("Phase 09", "Coupled Atmospheric Feature Ablation Experiments", "PENDING"),
        ("Phase 10", "Explainable AI & Atmospheric Sensitivity (SHAP Analysis)", "PENDING"),
        ("Phase 11", "Interactive Environmental Intelligence Dashboard (Streamlit UI/UX)", "PENDING"),
        ("Phase 12", "Deployment Readiness, Cloud Packaging & GitHub Finalization", "PENDING"),
    ]

    phase_cols = st.columns(2)
    for idx, (p_code, p_name, p_stat) in enumerate(phases):
        p_col = phase_cols[idx % 2]
        is_completed = (p_stat == "COMPLETED")
        badge_class = "completed" if is_completed else "pending"
        badge_text = "Completed" if is_completed else "Pending"
        with p_col:
            st.markdown(
                f"""
                <div style="background: {'#F0FDF4' if is_completed else '#FFFFFF'}; border: 1px solid {'#86EFAC' if is_completed else '#E2E8F0'}; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #0F172A; font-size: 0.85rem;">{p_code}:</strong>
                        <span style="color: #334155; font-size: 0.85rem; margin-left: 0.35rem;">{p_name}</span>
                    </div>
                    <span class="status-pill {badge_class}">{badge_text}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def view_placeholder(page_name: str):
    """Clean empty-state for modules awaiting subsequent development phases."""
    st.markdown(f"## {page_name}")
    st.markdown(
        f"""
        <div class="empty-state">
            <h3 style="color: #0F172A; margin: 0 0 0.5rem 0;">Component Staged for Implementation</h3>
            <p style="color: #64748B; max-width: 650px; margin: 0 auto 1.25rem; font-size: 0.95rem; line-height: 1.5;">
                This module (<strong>{page_name}</strong>) is scheduled for implementation in upcoming development phases.
                In adherence to scientific integrity principles, no simulated, fake, or synthetic measurements are presented.
            </p>
            <span class="status-pill pending">Awaiting Phase Pipeline</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def view_data_sources(config):
    """Render Data Sources & Scientific Information view."""
    st.markdown("## Data Sources & Coupled System Architecture")
    st.markdown(
        """
        AtmosCast integrates multi-agency environmental feeds to train and evaluate weather-coupled air quality forecasting models across Delhi NCR.
        """
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            ### Primary Scientific Data Feeds
            1. **OpenAQ API v3**
               - Standardized ambient air quality measurements from continuous monitoring stations.
               - Monitored parameters: $\\text{PM}_{2.5}$, $\\text{PM}_{10}$, $\\text{O}_3$, $\\text{NO}_2$, $\\text{SO}_2$, $\\text{CO}$.
            2. **CPCB India AQI Portal**
               - Central Pollution Control Board national standards, NAQI sub-index equations, and statutory limits.
            3. **Open-Meteo Historical & Forecast Weather API**
               - High-resolution planetary boundary layer (PBL) height.
               - Surface meteorology: 2m temperature, relative humidity, surface pressure, 10m wind speed and direction.
            4. **NASA FIRMS (Fire Information for Resource Management System)**
               - Satellite thermal anomaly and Fire Radiative Power (FRP) metrics from VIIRS/MODIS sensors across the northwest agricultural belt (Punjab & Haryana).
            """
        )
    with col2:
        st.markdown(
            """
            ### Coupled Modeling Scientific Integrity Notice
            > **Atmospheric Physics vs. Empirical ML:**  
            > AtmosCast couples meteorological variables with machine learning algorithms (XGBoost, Random Forest, Persistence Baseline). It is an empirical weather-aware statistical forecasting system, not a complete first-principles numerical photochemical transport solver (such as WRF-Chem or CMAQ).
            >
            > Photochemical transport simulators involve 3D Navier-Stokes fluid dynamics and gas-phase chemical kinetics equations. AtmosCast is designed to provide rapid, actionable, data-driven forecasts while making its physical assumptions transparent.
            """
        )


def main():
    """Main application loop."""
    config = get_cached_config()
    selected_page, selected_station = render_sidebar(config)

    if "1. Overview" in selected_page:
        view_overview(config, selected_station)
    elif "8. Data Sources" in selected_page:
        view_data_sources(config)
    else:
        view_placeholder(selected_page)


if __name__ == "__main__":
    main()
