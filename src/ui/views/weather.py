"""
Weather Analysis View for AtmosCast.
"""

from typing import Any, Dict
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.ui.theme import render_page_header, apply_custom_chart_theme


def render_weather_view(station: Dict[str, Any], station_df: pd.DataFrame):
    """
    Renders the Weather Analysis page with surface meteorology,
    atmospheric stability indicators, and weather-pollution coupling diagnostics.
    """
    render_page_header(
        kicker="SURFACE BOUNDARY-LAYER METEOROLOGY & DISPERSION",
        title=f"Atmospheric Diagnostics & Stability — {station['name']}",
        subtitle=f"Coupled surface weather dynamics, ventilation velocity, and thermal inversion indicators driving particulate concentration over Delhi NCR.",
    )

    # Weather KPI Cards
    w1, w2, w3, w4 = st.columns(4)
    with w1:
        st.metric(
            "Temperature (2m)",
            f"{station_df['temperature_2m'].iloc[-1]:.1f} °C",
            delta=f"Period Mean: {station_df['temperature_2m'].mean():.1f} °C",
            delta_color="off",
        )
    with w2:
        st.metric(
            "Relative Humidity",
            f"{station_df['relative_humidity_2m'].iloc[-1]:.0f} %",
            delta=f"Period Mean: {station_df['relative_humidity_2m'].mean():.0f} %",
            delta_color="off",
        )
    with w3:
        st.metric(
            "Wind Speed (10m)",
            f"{station_df['wind_speed_10m'].iloc[-1]:.1f} km/h",
            delta=f"Period Mean: {station_df['wind_speed_10m'].mean():.1f} km/h",
            delta_color="off",
        )
    with w4:
        st.metric(
            "Surface Pressure",
            f"{station_df['surface_pressure'].iloc[-1]:.0f} hPa",
            delta=f"Period Mean: {station_df['surface_pressure'].mean():.0f} hPa",
            delta_color="off",
        )

    st.markdown("---")

    # Multi-tab view: Meteorological Multi-Panel vs. Weather-Pollution Coupling
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.5rem;'>Atmospheric Time-Series & Cross-Variable Coupling</div>",
        unsafe_allow_html=True,
    )

    wt1, wt2 = st.tabs(["Surface Meteorology Panels", "Pollution-Weather Coupling Dynamics"])

    t_dates = pd.to_datetime(station_df["timestamp_ist"])

    with wt1:
        fig_multi = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Ambient Temperature (2m)",
                "Relative Humidity (%)",
                "10m Wind Speed (Ventilation Velocity)",
                "Surface Barometric Pressure (hPa)",
            ),
            vertical_spacing=0.18,
            horizontal_spacing=0.10,
        )

        # Temperature
        fig_multi.add_trace(
            go.Scatter(x=t_dates, y=station_df["temperature_2m"], name="Temp (2m)", line=dict(color="#DC2626", width=2)),
            row=1, col=1,
        )
        # Humidity
        fig_multi.add_trace(
            go.Scatter(x=t_dates, y=station_df["relative_humidity_2m"], name="RH (%)", line=dict(color="#2563EB", width=2)),
            row=1, col=2,
        )
        # Wind Speed
        fig_multi.add_trace(
            go.Scatter(x=t_dates, y=station_df["wind_speed_10m"], name="Wind Speed", line=dict(color="#0D9488", width=2)),
            row=2, col=1,
        )
        fig_multi.add_hline(
            y=5.4,
            line_dash="dash",
            line_color="#F59E0B",
            line_width=1.5,
            annotation_text="Stagnation Boundary (< 1.5 m/s)",
            annotation_font=dict(family="JetBrains Mono, monospace", size=9, color="#F59E0B"),
            row=2, col=1,
        )
        # Pressure
        fig_multi.add_trace(
            go.Scatter(x=t_dates, y=station_df["surface_pressure"], name="Pressure", line=dict(color="#7C3AED", width=2)),
            row=2, col=2,
        )

        fig_multi = apply_custom_chart_theme(fig_multi, height=500, show_legend=False)

        for r in [1, 2]:
            for c in [1, 2]:
                fig_multi.update_xaxes(gridcolor="#E2E8F0", row=r, col=c)
                fig_multi.update_yaxes(gridcolor="#E2E8F0", row=r, col=c)

        st.plotly_chart(fig_multi, use_container_width=True)

    with wt2:
        # Scatter plots coupling weather with PM2.5
        sc_col1, sc_col2 = st.columns(2)

        with sc_col1:
            fig_sc1 = go.Figure()
            fig_sc1.add_trace(go.Scatter(
                x=station_df["wind_speed_10m"],
                y=station_df["pm25"],
                mode="markers",
                marker=dict(size=7, color="#0D9488", opacity=0.7),
                hovertemplate="Wind Speed: %{x:.1f} km/h<br>PM2.5: <b>%{y:.1f} µg/m³</b><extra></extra>",
            ))
            fig_sc1.add_vline(
                x=5.4,
                line_dash="dash",
                line_color="#EF6461",
                annotation_text="Stagnation (1.5 m/s)",
                annotation_position="top right",
            )
            fig_sc1.update_xaxes(title="10m Wind Speed (km/h)")
            fig_sc1.update_yaxes(title="PM2.5 Concentration (µg/m³)")
            fig_sc1 = apply_custom_chart_theme(fig_sc1, height=400, title="PM2.5 vs Wind Velocity (Ventilation Collapse)")
            st.plotly_chart(fig_sc1, use_container_width=True)

        with sc_col2:
            fig_sc2 = go.Figure()
            fig_sc2.add_trace(go.Scatter(
                x=station_df["relative_humidity_2m"],
                y=station_df["pm25"],
                mode="markers",
                marker=dict(size=7, color="#2563EB", opacity=0.7),
                hovertemplate="RH: %{x:.0f}%<br>PM2.5: <b>%{y:.1f} µg/m³</b><extra></extra>",
            ))
            fig_sc2.add_vline(
                x=85.0,
                line_dash="dash",
                line_color="#F59E0B",
                annotation_text="Fog / Secondary Aerosol Growth (>85%)",
                annotation_position="top left",
            )
            fig_sc2.update_xaxes(title="Relative Humidity (%)")
            fig_sc2.update_yaxes(title="PM2.5 Concentration (µg/m³)")
            fig_sc2 = apply_custom_chart_theme(fig_sc2, height=400, title="PM2.5 vs Relative Humidity (Moisture Catalyst)")
            st.plotly_chart(fig_sc2, use_container_width=True)

    # Atmospheric Stability & Boundary Layer Diagnostics
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin: 1.5rem 0 0.5rem;'>Thermodynamic Inversion & Stagnation Diagnostics</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="intel-brief">
            <div class="intel-brief-title">Scientific Transparency: Boundary-Layer Height Availability</div>
            <p class="intel-brief-body">
                <strong>Status: Direct PBL Height Unavailable in Reanalysis Archive Extract.</strong><br>
                Raw Planetary Boundary Layer (PBL) height was absent from the historical numerical archive extract for early January 2024. In accordance with AtmosCast scientific integrity standards, no synthetic or fabricated PBL heights are substituted. Instead, validated surface thermodynamic proxies (Dew Point Depression and Wind Stagnation Share) are computed directly from calibrated ground sensors below.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st_col1, st_col2, st_col3 = st.columns(3)
    dew_depression = station_df["temperature_2m"] - station_df["dew_point_2m"]
    stagnation_share = (station_df["wind_speed_10m"] < 5.4).mean() * 100.0

    with st_col1:
        st.markdown(
            f"""
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Thermodynamics</span>
                    <span class="status-pill moderate"><span class="pill-dot"></span>Saturation Proxy</span>
                </div>
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.9rem; font-weight: 700; color: #172B4D; margin-top: 0.3rem;">Dew Point Depression (T - Td)</div>
                <div class="metric-value-box">
                    <span class="metric-number">{dew_depression.mean():.1f}</span>
                    <span class="metric-unit">°C Mean</span>
                </div>
                <div class="card-footer-meta">
                    Depression &lt; 2°C indicates near-saturation fog, accelerating aqueous secondary aerosol formation.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st_col2:
        st.markdown(
            f"""
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Dispersion Trap</span>
                    <span class="status-pill severe"><span class="pill-dot"></span>Calm Velocity</span>
                </div>
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.9rem; font-weight: 700; color: #172B4D; margin-top: 0.3rem;">Ventilation Stagnation Share</div>
                <div class="metric-value-box">
                    <span class="metric-number">{stagnation_share:.1f}</span>
                    <span class="metric-unit">% Hours &lt; 1.5 m/s</span>
                </div>
                <div class="card-footer-meta">
                    Proportion of time near-surface ventilation is insufficient to displace local emissions.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st_col3:
        mean_pres = station_df["surface_pressure"].mean()
        st.markdown(
            f"""
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Synoptic Pressure</span>
                    <span class="status-pill good"><span class="pill-dot"></span>Anticyclonic</span>
                </div>
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.9rem; font-weight: 700; color: #172B4D; margin-top: 0.3rem;">Barometric Regime</div>
                <div class="metric-value-box">
                    <span class="metric-number">{mean_pres:.0f}</span>
                    <span class="metric-unit">hPa Mean</span>
                </div>
                <div class="card-footer-meta">
                    High pressure anticyclonic ridge generates strong subsidence and clear-sky nocturnal radiative cooling.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
