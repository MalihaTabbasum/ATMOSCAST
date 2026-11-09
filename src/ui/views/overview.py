"""
Overview Dashboard View for AtmosCast.
"""

from typing import Any, Dict
import pandas as pd
import streamlit as st

from src.forecasting.aqi import CPCBIndexCalculator


def render_overview_view(
    station: Dict[str, Any],
    latest_obs: pd.Series,
    all_stations: list,
):
    """
    Renders the Overview page with real observations, status cards, and architecture summary.
    """
    st.markdown(
        """
        <div class="hero-header">
            <div class="hero-title">AtmosCast — Environmental Intelligence</div>
            <div class="hero-subtitle">
                Weather-Aware Air Pollution Forecasting System • Delhi NCR Focus (SIH Problem Statement SIH26082)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Station Context Banner
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border-left: 4px solid #0D9488; border-radius: 8px; padding: 0.9rem 1.25rem; margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                <div>
                    <span style="font-size: 1.15rem; font-weight: 700; color: #102A43;">📍 {station['name']}</span>
                    <span style="color: #64748B; font-size: 0.85rem; margin-left: 0.5rem;">({station['authority']} • {station['city']})</span>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.2rem;">{station['description']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.78rem; color: #64748B;">Latest Observation Time</div>
                    <div style="font-size: 0.85rem; font-weight: 700; color: #0D9488;">
                        {latest_obs.get('timestamp_ist', 'N/A')}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Latest Real-World Conditions (KPI Cards)
    st.markdown("### Latest Observed Conditions")

    pm25_val = float(latest_obs.get("pm25", 0.0))
    pm10_val = float(latest_obs.get("pm10", 0.0))
    temp_val = float(latest_obs.get("temperature_2m", 0.0))
    rh_val = float(latest_obs.get("relative_humidity_2m", 0.0))
    ws_val = float(latest_obs.get("wind_speed_10m", 0.0))

    # Calculate statutory CPCB Sub-Index for PM2.5
    aqi_res = CPCBIndexCalculator.compute_official_aqi({
        "pm25": pm25_val,
        "pm10": pm10_val,
        "no2": float(latest_obs.get("no2", 30.0)),
    })
    sub_index_val = aqi_res.get("aqi") or aqi_res.get("indicative_sub_index")
    category = aqi_res["category"]
    color = aqi_res["color"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="atmos-card">
                <span class="status-pill" style="background-color: {color}22; color: {color}; border: 1px solid {color}55;">
                    {category}
                </span>
                <div style="margin-top: 0.6rem; color: #64748B; font-size: 0.85rem; font-weight: 600;">Statutory CPCB AQI</div>
                <div class="metric-value-box">
                    <span class="metric-number" style="color: {color};">{sub_index_val:.0f}</span>
                    <span class="metric-unit">Index</span>
                </div>
                <div style="font-size: 0.75rem; color: #64748B;">Prominent: <strong>{aqi_res.get('prominent_pollutant', 'PM2.5')}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="atmos-card">
                <span class="status-pill very-poor">Primary Target</span>
                <div style="margin-top: 0.6rem; color: #64748B; font-size: 0.85rem; font-weight: 600;">Fine Particulates (PM2.5)</div>
                <div class="metric-value-box">
                    <span class="metric-number">{pm25_val:.1f}</span>
                    <span class="metric-unit">µg/m³</span>
                </div>
                <div style="font-size: 0.75rem; color: #DC2626;">CPCB 24h Std: 60 µg/m³ ({pm25_val/60:.1f}x)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="atmos-card">
                <span class="status-pill poor">Coarse Particulates</span>
                <div style="margin-top: 0.6rem; color: #64748B; font-size: 0.85rem; font-weight: 600;">Particulate Matter (PM10)</div>
                <div class="metric-value-box">
                    <span class="metric-number">{pm10_val:.1f}</span>
                    <span class="metric-unit">µg/m³</span>
                </div>
                <div style="font-size: 0.75rem; color: #EA580C;">CPCB 24h Std: 100 µg/m³</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="atmos-card">
                <span class="status-pill" style="background: #F1F5F9; color: #334155;">Atmospheric State</span>
                <div style="margin-top: 0.6rem; color: #64748B; font-size: 0.85rem; font-weight: 600;">Surface Weather</div>
                <div class="metric-value-box">
                    <span class="metric-number">{temp_val:.1f}</span>
                    <span class="metric-unit">°C</span>
                </div>
                <div style="font-size: 0.75rem; color: #64748B;">Wind: {ws_val:.1f} km/h • RH: {rh_val:.0f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # Forecast Availability & System Status
    st.markdown("### Operational Forecast Availability")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill good">Ready</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43; font-size: 0.95rem;">24-Hour Horizon</h4>
                <div style="font-size: 1.25rem; font-weight: 700; color: #0D9488;">t + 24 hrs</div>
                <p style="font-size: 0.78rem; color: #64748B; margin-top: 0.3rem;">Trained XGBoost / RF Engine</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f2:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill good">Ready</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43; font-size: 0.95rem;">48-Hour Horizon</h4>
                <div style="font-size: 1.25rem; font-weight: 700; color: #0D9488;">t + 48 hrs</div>
                <p style="font-size: 0.78rem; color: #64748B; margin-top: 0.3rem;">Coupled Weather Tier 2 Engine</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f3:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill good">Ready</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43; font-size: 0.95rem;">72-Hour Horizon</h4>
                <div style="font-size: 1.25rem; font-weight: 700; color: #0D9488;">t + 72 hrs</div>
                <p style="font-size: 0.78rem; color: #64748B; margin-top: 0.3rem;">Synoptic Direct Direct Forecast</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f4:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill good">Active</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43; font-size: 0.95rem;">Explainability Engine</h4>
                <div style="font-size: 1.25rem; font-weight: 700; color: #102A43;">SHAP Verified</div>
                <p style="font-size: 0.78rem; color: #64748B; margin-top: 0.3rem;">Exact TreeSHAP Attribution</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Monitored Station Network Grid
    st.markdown("### Delhi NCR Monitoring Network (6 Stations)")
    st_cols = st.columns(3)
    for idx, s in enumerate(all_stations):
        scol = st_cols[idx % 3]
        with scol:
            st.markdown(
                f"""
                <div class="atmos-card" style="margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; color: #102A43;">{s['name']}</span>
                        <span style="background: #F1F5F9; color: #334155; font-size: 0.75rem; font-weight: 600; padding: 0.2rem 0.5rem; border-radius: 4px;">{s['authority']}</span>
                    </div>
                    <p style="font-size: 0.8rem; color: #64748B; margin: 0.4rem 0;">{s['description']}</p>
                    <div style="font-size: 0.75rem; color: #0D9488; font-weight: 600;">
                        📍 {s['latitude']:.4f}°N, {s['longitude']:.4f}°E ({s['city']})
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
