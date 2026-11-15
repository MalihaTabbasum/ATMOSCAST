"""
AtmosCast: Weather-Aware Air Pollution Forecasting System
Main Streamlit Application Dashboard

Delhi NCR Focus (SIH Problem Statement SIH26082)
Deployment: Streamlit Community Cloud & Local Execution
"""

from pathlib import Path
import sys
import pandas as pd
import streamlit as st

# Resolve project root from app.py's location — works locally and on Streamlit Cloud
_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from src.utils.config import load_config, get_stations
from src.ui.theme import CUSTOM_CSS, render_command_topbar
from src.ui.views.overview import render_overview_view
from src.ui.views.air_quality import render_air_quality_view
from src.ui.views.forecast import render_forecast_view
from src.ui.views.weather import render_weather_view
from src.ui.views.episodes import render_episodes_view
from src.ui.views.performance import render_performance_view
from src.ui.views.explainability import render_explainability_view
from src.ui.views.about import render_about_view

# ── Streamlit page configuration ───────────────────────────────────────────────
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
def load_analytical_dataset() -> pd.DataFrame:
    """Load the cleaned merged analytical dataset.

    Resolution order (supports both local dev and Streamlit Cloud):
    1. <app_dir>/data/processed/merged_delhi_ncr_hourly.csv  (repo-relative)
    2. data/processed/merged_delhi_ncr_hourly.csv            (cwd fallback)
    """
    candidates = [
        _APP_DIR / "data" / "processed" / "merged_delhi_ncr_hourly.csv",
        Path("data") / "processed" / "merged_delhi_ncr_hourly.csv",
    ]
    for data_path in candidates:
        if data_path.exists():
            try:
                df = pd.read_csv(data_path)
                return df
            except Exception as exc:
                st.warning(f"Dataset found at {data_path} but could not be read: {exc}")
                return pd.DataFrame()

    # Dataset not found — show a user-friendly, actionable message
    st.error(
        "**Dataset not found.**  \n"
        "The file `data/processed/merged_delhi_ncr_hourly.csv` was not found.  \n\n"
        "If running locally, re-run the preprocessing pipeline:  \n"
        "```bash\n"
        "python -m src.preprocessing.pipeline\n"
        "```\n\n"
        "If this is a fresh clone, ensure the processed data file is present in the repository."
    )
    return pd.DataFrame()


def render_sidebar(config, df: pd.DataFrame):
    """Render consistent sidebar navigation and system information."""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding-bottom: 0.85rem; border-bottom: 1px solid rgba(255, 255, 255, 0.12); margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 800; font-size: 1.25rem; letter-spacing: -0.02em; color: #FFFFFF;">
                        ATMOSCAST
                    </span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; font-weight: 700; color: #38BDF8; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); padding: 0.15rem 0.45rem; border-radius: 9999px;">
                        v1.0 • LIVE
                    </span>
                </div>
                <div style="font-size: 0.76rem; color: #94A3B8; margin-top: 0.35rem; line-height: 1.4;">
                    Weather-Aware Air Pollution Forecasting
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #0D9488; margin-top: 0.25rem;">
                    SIH26082 • DELHI NCR FOCUS
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='font-family: \"JetBrains Mono\", monospace; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #94A3B8; margin-bottom: 0.4rem;'>Observatory Console</div>",
            unsafe_allow_html=True,
        )
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

        st.markdown("<hr style='border-color: rgba(255, 255, 255, 0.1); margin: 1rem 0;'>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-family: \"JetBrains Mono\", monospace; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #94A3B8; margin-bottom: 0.4rem;'>Monitoring Station</div>",
            unsafe_allow_html=True,
        )
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
            <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 8px; padding: 0.75rem; margin-top: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
                    <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 0.85rem; color: #FFFFFF;">{selected_station['name']}</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; font-weight: 600; color: #10B981; background: rgba(16, 185, 129, 0.2); border: 1px solid rgba(16, 185, 129, 0.4); padding: 0.1rem 0.4rem; border-radius: 4px;">ACTIVE</span>
                </div>
                <div style="font-size: 0.75rem; color: #94A3B8;">{selected_station['authority']} • {selected_station['city']}</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #38BDF8; margin-top: 0.25rem;">
                    📍 {selected_station['latitude']:.4f}°N, {selected_station['longitude']:.4f}°E
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<hr style='border-color: rgba(255, 255, 255, 0.1); margin: 1rem 0;'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="font-size: 0.74rem; color: #94A3B8; line-height: 1.5; background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 0.65rem;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; font-weight: 700; color: #CBD5E1; text-transform: uppercase; margin-bottom: 0.25rem;">System Architecture</div>
                <strong style="color: #F8FAFC;">Engine:</strong> Direct XGBoost (Tier 2)<br>
                <strong style="color: #F8FAFC;">Horizons:</strong> 24h • 48h • 72h direct<br>
                <strong style="color: #F8FAFC;">CPCB Standard:</strong> Piecewise NAQI<br>
                <strong style="color: #F8FAFC;">Explainability:</strong> Exact TreeSHAP
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

    # Render persistent command topbar across all pages
    coords_str = f"{selected_station['latitude']:.4f}°N, {selected_station['longitude']:.4f}°E"
    timestamp_str = str(latest_obs.get('timestamp_ist', '2024-01-07 23:00 IST'))
    render_command_topbar(
        station_name=selected_station['name'],
        station_code=selected_station['id'].upper(),
        coords=coords_str,
        timestamp_ist=timestamp_str,
    )

    # Route navigation
    if selected_page == "1. Overview":
        render_overview_view(selected_station, latest_obs, all_stations, df)
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
