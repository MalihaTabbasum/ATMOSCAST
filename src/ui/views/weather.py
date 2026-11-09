"""
Weather Analysis View for AtmosCast.
"""

from typing import Any, Dict
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


def render_weather_view(station: Dict[str, Any], station_df: pd.DataFrame):
    """
    Renders the Weather Analysis page with surface meteorology and atmospheric stability indicators.
    """
    st.markdown(
        f"""
        <div class="hero-header">
            <div class="hero-title">Boundary-Layer Meteorology — {station['name']}</div>
            <div class="hero-subtitle">
                Surface weather observations and atmospheric dispersion dynamics driving Delhi NCR airshed stagnation
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Weather KPI Cards
    w1, w2, w3, w4 = st.columns(4)
    with w1:
        st.metric("Temperature (2m)", f"{station_df['temperature_2m'].iloc[-1]:.1f} °C", delta=f"{station_df['temperature_2m'].mean():.1f} °C avg")
    with w2:
        st.metric("Relative Humidity", f"{station_df['relative_humidity_2m'].iloc[-1]:.0f} %", delta=f"{station_df['relative_humidity_2m'].mean():.0f} % avg")
    with w3:
        st.metric("Wind Speed (10m)", f"{station_df['wind_speed_10m'].iloc[-1]:.1f} km/h", delta=f"{station_df['wind_speed_10m'].mean():.1f} km/h avg")
    with w4:
        st.metric("Surface Pressure", f"{station_df['surface_pressure'].iloc[-1]:.0f} hPa")

    st.markdown("---")

    # Multi-Panel Meteorological Plot
    st.markdown("### Surface Meteorological Time-Series")

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Ambient Temperature (2m)", "Relative Humidity (%)", "10m Wind Speed (Dispersion Velocity)", "Surface Barometric Pressure"),
        vertical_spacing=0.15,
        horizontal_spacing=0.10,
    )

    t_dates = pd.to_datetime(station_df["timestamp_ist"])

    # Temperature
    fig.add_trace(go.Scatter(x=t_dates, y=station_df["temperature_2m"], name="Temp (2m)", line=dict(color="#EF4444", width=2)), row=1, col=1)
    # Humidity
    fig.add_trace(go.Scatter(x=t_dates, y=station_df["relative_humidity_2m"], name="RH (%)", line=dict(color="#3B82F6", width=2)), row=1, col=2)
    # Wind Speed
    fig.add_trace(go.Scatter(x=t_dates, y=station_df["wind_speed_10m"], name="Wind Speed", line=dict(color="#0D9488", width=2)), row=2, col=1)
    fig.add_hline(y=5.0, line_dash="dash", line_color="#F59E0B", annotation_text="Stagnation (< 5 km/h)", row=2, col=1)
    # Pressure
    fig.add_trace(go.Scatter(x=t_dates, y=station_df["surface_pressure"], name="Pressure", line=dict(color="#8B5CF6", width=2)), row=2, col=2)

    fig.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(family="Inter, sans-serif", color="#1E293B"),
        height=520,
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
    )
    for r in [1, 2]:
        for c in [1, 2]:
            fig.update_xaxes(gridcolor="#E2E8F0", row=r, col=c)
            fig.update_yaxes(gridcolor="#E2E8F0", row=r, col=c)

    st.plotly_chart(fig, use_container_width=True)

    # Atmospheric Stability & Inversion Diagnostic Card
    st.markdown("### Planetary Boundary Layer & Atmospheric Inversion Analysis")

    st.info(
        "ℹ️ **Scientific Data Transparency:** Raw Planetary Boundary Layer (PBL) height was unavailable in the historical Open-Meteo reanalysis archive extract for early January 2024. In accordance with AtmosCast scientific integrity guidelines, no simulated or fabricated heights are substituted. Instead, validated surface thermodynamic proxies are presented below."
    )

    st_col1, st_col2, st_col3 = st.columns(3)
    dew_depression = station_df["temperature_2m"] - station_df["dew_point_2m"]
    stagnation_share = (station_df["wind_speed_10m"] < 5.0).mean() * 100.0

    with st_col1:
        st.markdown(
            f"""
            <div class="atmos-card">
                <span class="status-pill moderate">Moisture Trapping</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43;">Dew Point Depression (T - Td)</h4>
                <div class="metric-number" style="font-size: 1.5rem;">{dew_depression.mean():.1f} °C</div>
                <p style="font-size: 0.78rem; color: #64748B; margin-top: 0.3rem;">Low values (< 2°C) indicate surface air near saturation, fostering fog and secondary aerosol formation.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st_col2:
        st.markdown(
            f"""
            <div class="atmos-card">
                <span class="status-pill very-poor">Horizontal Stagnation</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43;">Wind Stagnation Rate</h4>
                <div class="metric-number" style="font-size: 1.5rem; color: #DC2626;">{stagnation_share:.1f}%</div>
                <p style="font-size: 0.78rem; color: #64748B; margin-top: 0.3rem;">Percentage of hours with calm surface winds (< 5 km/h) where horizontal dispersion breaks down.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st_col3:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill" style="background: #F1F5F9; color: #334155;">Atmospheric Guardrail</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43;">Inversion Detection Rule</h4>
                <div style="font-size: 0.95rem; font-weight: 700; color: #102A43;">Surface Proxy Only</div>
                <p style="font-size: 0.78rem; color: #64748B; margin-top: 0.3rem;">True thermal inversions (dT/dz > 0) require vertical radiosonde soundings. Surface cold pools act as risk proxies, not confirmed detections.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
