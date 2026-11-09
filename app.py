"""
AtmosCast: Weather-Aware Air Pollution Forecasting System
Streamlit Dashboard Entry Point

Delhi NCR Focus (SIH26082)
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

    /* Card styling */
    .atmos-card {
        background: #FFFFFF;
        border: 1px solid var(--border-slate);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .atmos-card:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }

    /* Metric pill */
    .status-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.025em;
    }
    .status-pill.ready {
        background-color: #ECFDF5;
        color: #059669;
        border: 1px solid #A7F3D0;
    }
    .status-pill.pending {
        background-color: #EFF6FF;
        color: #2563EB;
        border: 1px solid #BFDBFE;
    }

    /* Station badge */
    .station-badge {
        background: #F1F5F9;
        color: #334155;
        font-size: 0.85rem;
        padding: 0.35rem 0.75rem;
        border-radius: 6px;
        display: inline-block;
        margin: 0.2rem;
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
            <div style="padding-bottom: 0.5rem; border-bottom: 1px solid #E2E8F0;">
                <h2 style="color: #0F172A; margin: 0; font-weight: 700; font-size: 1.4rem;">
                    🌫️ AtmosCast
                </h2>
                <p style="color: #64748B; font-size: 0.82rem; margin: 0.2rem 0 0 0;">
                    Weather-Aware Air Pollution Forecasting<br>
                    <span style="color: #0D9488; font-weight: 500;">SIH26082 • Delhi NCR Focus</span>
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
        st.markdown("### Monitored Domain")
        stations = get_stations(config)
        st.caption(f"📍 **{len(stations)} Stations Configured** in Delhi NCR")
        selected_station = st.selectbox(
            "Selected Station",
            options=[s["name"] for s in stations],
            index=0,
        )

        st.markdown("---")
        st.markdown(
            """
            <div style="font-size: 0.78rem; color: #64748B;">
                <strong>System Version:</strong> v1.0.0<br>
                <strong>Phase:</strong> Workspace Setup Complete<br>
                <strong>Engine:</strong> Open-Meteo & OpenAQ Ready
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_page, selected_station


def view_overview(config, station_name):
    """Render Overview dashboard page."""
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h1 style="color: #0F172A; font-size: 2rem; font-weight: 800; margin-bottom: 0.25rem;">
                Environmental Intelligence Overview
            </h1>
            <p style="color: #64748B; font-size: 1rem; margin-top: 0;">
                Coupled atmospheric and air quality surveillance for Delhi NCR monitoring stations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Status Notification Box
    st.info(
        "🚀 **System Workspace Ready**: AtmosCast architecture and configuration have been initialized. "
        "The project is currently awaiting **Phase 1 (Data Collection & Pipeline)** instruction to fetch real-world measurements.",
        icon="ℹ️",
    )

    # Top KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill ready">Ready</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #0F172A;">Target Pollutants</h4>
                <p style="font-size: 1.5rem; font-weight: 700; color: #0D9488; margin: 0;">PM2.5, PM10</p>
                <p style="font-size: 0.8rem; color: #64748B; margin: 0.2rem 0 0;">O3, NO2, SO2, CO configured</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill ready">Ready</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #0F172A;">Forecast Horizons</h4>
                <p style="font-size: 1.5rem; font-weight: 700; color: #0F172A; margin: 0;">24, 48, 72 hrs</p>
                <p style="font-size: 0.8rem; color: #64748B; margin: 0.2rem 0 0;">Multi-step chronological model</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill ready">Ready</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #0F172A;">Coupled Meteorology</h4>
                <p style="font-size: 1.5rem; font-weight: 700; color: #0F172A; margin: 0;">PBL & Inversion</p>
                <p style="font-size: 0.8rem; color: #64748B; margin: 0.2rem 0 0;">Ventilation coefficient & wind</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill pending">Phase 1 Pending</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #0F172A;">Observation Feed</h4>
                <p style="font-size: 1.5rem; font-weight: 700; color: #64748B; margin: 0;">Standby</p>
                <p style="font-size: 0.8rem; color: #64748B; margin: 0.2rem 0 0;">Awaiting pipeline ingestion</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Configured Monitoring Stations")
    stations = get_stations(config)
    cols = st.columns(3)
    for idx, st_item in enumerate(stations):
        col = cols[idx % 3]
        with col:
            st.markdown(
                f"""
                <div class="atmos-card">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <h4 style="margin: 0; color: #0F172A; font-weight: 700;">{st_item['name']}</h4>
                        <span class="station-badge">{st_item['authority']}</span>
                    </div>
                    <p style="font-size: 0.82rem; color: #64748B; margin: 0.4rem 0;">{st_item['description']}</p>
                    <p style="font-size: 0.78rem; color: #0D9488; margin: 0;">
                        📍 Lat: {st_item['latitude']:.4f}°N | Lon: {st_item['longitude']:.4f}°E ({st_item['city']})
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def view_placeholder(page_name: str):
    """Clean placeholder for sections pending subsequent implementation phases."""
    st.markdown(f"## {page_name}")
    st.markdown(
        f"""
        <div class="atmos-card" style="padding: 2.5rem; text-align: center;">
            <h3 style="color: #0F172A; margin-bottom: 0.5rem;">Component Staged for Implementation</h3>
            <p style="color: #64748B; max-width: 600px; margin: 0 auto 1.5rem;">
                This module (<strong>{page_name}</strong>) is mapped to upcoming development phases per the controlled development plan.
                In adherence to project principles, no fake observations, mock forecasts, or synthetic numbers are generated.
            </p>
            <span class="status-pill pending">Phase Pending</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def view_data_sources(config):
    """Render Data Sources & Project Information view."""
    st.markdown("## Data Sources & Project Architecture")
    st.markdown(
        """
        AtmosCast integrates multi-agency environmental feeds to train and evaluate weather-coupled air quality forecasting models.
        """
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            ### Primary Scientific Data Sources
            1. **OpenAQ API v3**
               - Source for standardized historical ground-level air quality observations.
               - Pollutants: PM2.5, PM10, O3, NO2, SO2, CO.
            2. **CPCB India AQI Portal**
               - National reference standard for NAQI sub-index breakpoints and statutory limits.
            3. **Open-Meteo Historical & Forecast Weather API**
               - High-resolution atmospheric variables: 2m temperature, relative humidity, surface pressure, 10m wind vector.
               - Atmospheric boundary layer (PBL) height.
            4. **NASA FIRMS (Fire Information for Resource Management System)**
               - Satellite thermal anomaly and Fire Radiative Power (FRP) metrics from VIIRS/MODIS sensors over the northwest agricultural corridor.
            """
        )
    with col2:
        st.markdown(
            """
            ### Coupled Modeling Disclaimer
            > **Scientific Integrity Notice:** AtmosCast utilizes advanced gradient-boosted machine learning (XGBoost) and empirical atmospheric interaction features (ventilation coefficients, thermal lapse rate inversion proxies, stubble fire indices).
            >
            > While informed by atmospheric physics, this is an empirical Machine Learning model and does **not** substitute for a complete numerical photochemical transport solver (such as WRF-Chem or CMAQ).
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
