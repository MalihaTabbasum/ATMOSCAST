"""
AtmosCast: Weather-Aware Air Pollution Forecasting System
Main Streamlit Application Dashboard (Phase 9)

Delhi NCR Focus (SIH Problem Statement SIH26082)
"""

from pathlib import Path
import sys
import pandas as pd
import streamlit as st

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.utils.config import load_config, get_stations
from src.ui.theme import CUSTOM_CSS
from src.ui.views.overview import render_overview_view
from src.ui.views.air_quality import render_air_quality_view
from src.ui.views.forecast import render_forecast_view
from src.ui.views.weather import render_weather_view
from src.ui.views.episodes import render_episodes_view
from src.ui.views.performance import render_performance_view
from src.ui.views.explainability import render_explainability_view
from src.ui.views.about import render_about_view

# Page configuration
st.set_page_config(
    page_title="AtmosCast | Environmental Intelligence",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified design system CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data
def get_cached_config():
    """Load configuration safely with caching."""
    return load_config()


@st.cache_data
def load_analytical_dataset():
    """Loads the verified cleaned merged analytical dataset."""
    data_path = Path("data/processed/merged_delhi_ncr_hourly.csv")
    if not data_path.exists():
        st.error(f"Processed dataset not found at {data_path}. Please verify Phase 3 preprocessing.")
        return pd.DataFrame()
    return pd.read_csv(data_path)


def render_sidebar(config, df: pd.DataFrame):
    """Render consistent sidebar navigation and system information."""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding-bottom: 0.75rem; border-bottom: 1px solid #E2E8F0;">
                <h2 style="color: #102A43; margin: 0; font-weight: 800; font-size: 1.35rem; display: flex; align-items: center; gap: 0.5rem;">
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
            "2. Air Quality Monitoring",
            "3. 72-Hour Forecast",
            "4. Weather Analysis",
            "5. Pollution Episode Analysis",
            "6. Model Performance",
            "7. Explainable AI",
            "8. Data Sources and About",
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
                <div style="font-weight: 600; color: #102A43;">{selected_station['name']}</div>
                <div style="color: #64748B;">{selected_station['authority']} • {selected_station['city']}</div>
                <div style="color: #0D9488; margin-top: 0.25rem;">
                    📍 {selected_station['latitude']:.4f}°N, {selected_station['longitude']:.4f}°E
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            """
            <div style="font-size: 0.78rem; color: #64748B; line-height: 1.5;">
                <strong>Architecture:</strong> Coupled ML & Meteorology<br>
                <strong>Engine:</strong> XGBoost Multi-Horizon<br>
                <strong>Horizons:</strong> 24h • 48h • 72h<br>
                <strong>Status:</strong> Operational Dashboard
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_page, selected_station


def main():
    config = get_cached_config()
    df = load_analytical_dataset()

    selected_page, selected_station = render_sidebar(config, df)

    if df.empty:
        st.warning("No data available to display. Please verify processed data directory.")
        return

    # Filter station slice
    station_df = df[df["station_id"] == selected_station["id"]].copy()
    if station_df.empty:
        station_df = df.copy()

    latest_obs = station_df.iloc[-1]
    all_stations = get_stations(config)

    # Route navigation
    if selected_page == "1. Overview":
        render_overview_view(selected_station, latest_obs, all_stations)
    elif selected_page == "2. Air Quality Monitoring":
        render_air_quality_view(selected_station, station_df)
    elif selected_page == "3. 72-Hour Forecast":
        render_forecast_view(selected_station, station_df)
    elif selected_page == "4. Weather Analysis":
        render_weather_view(selected_station, station_df)
    elif selected_page == "5. Pollution Episode Analysis":
        render_episodes_view(selected_station, station_df)
    elif selected_page == "6. Model Performance":
        render_performance_view()
    elif selected_page == "7. Explainable AI":
        render_explainability_view(station_df)
    elif selected_page == "8. Data Sources and About":
        render_about_view()


if __name__ == "__main__":
    main()
