"""
Overview Dashboard View for AtmosCast.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.forecasting.aqi import CPCBIndexCalculator
from src.ui.theme import render_page_header, render_health_alert, apply_custom_chart_theme


def render_overview_view(
    station: Dict[str, Any],
    latest_obs: pd.Series,
    all_stations: List[Dict[str, Any]],
    df: Optional[pd.DataFrame] = None,
):
    """
    Renders the Overview page with real observations, status cards, interactive map, and architecture summary.
    """
    render_page_header(
        kicker="AIRSHED SURVEILLANCE & SYSTEM OVERVIEW",
        title="Delhi NCR Atmospheric Observatory",
        subtitle="Continuous ground-level pollutant surveillance, coupled boundary-layer thermodynamics, and multi-horizon forecasting availability across 6 statutory CAAQMS stations.",
    )

    # Station Context Strip
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #0D9488; border-radius: 8px; padding: 0.85rem 1.15rem; margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(15,23,42,0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                <div>
                    <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D;">{station['name']}</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; color: #64748B; margin-left: 0.5rem;">({station['authority']} • {station['city']})</span>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 0.2rem;">{station['description']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #64748B;">Latest Validated Telemetry</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; font-weight: 700; color: #0D9488;">
                        {latest_obs.get('timestamp_ist', '2024-01-07 23:00 IST')}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Telemetry Observations (6 KPI Cards)
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin: 0.75rem 0 0.5rem;'>Key Environmental Indicators & Current Telemetry</div>",
        unsafe_allow_html=True,
    )

    pm25_val = float(latest_obs.get("pm25", 0.0))
    pm10_val = float(latest_obs.get("pm10", 0.0))
    o3_val = latest_obs.get("o3", None)
    temp_val = float(latest_obs.get("temperature_2m", 0.0))
    rh_val = float(latest_obs.get("relative_humidity_2m", 0.0))
    ws_val = float(latest_obs.get("wind_speed_10m", 0.0))

    # Calculate statutory CPCB Sub-Index for PM2.5
    aqi_res = CPCBIndexCalculator.compute_official_aqi({
        "pm25": pm25_val,
        "pm10": pm10_val,
        "no2": float(latest_obs.get("no2", 30.0)),
    })
    sub_index_val = aqi_res.get("aqi") or aqi_res.get("indicative_sub_index") or 0.0
    category = aqi_res["category"]
    color = aqi_res["color"]

    # Statutory Public Health Alert & GRAP Banner
    render_health_alert(
        aqi_val=sub_index_val,
        category=category,
        prominent=aqi_res.get("prominent_pollutant", "PM2.5"),
    )

    # Row 1: 3 Primary Pollutants (PM2.5, PM10, Ozone)
    k1, k2, k3 = st.columns(3)
    with k1:
        pm25_mult = pm25_val / 60.0 if pm25_val > 0 else 0.0
        st.markdown(
            f"""
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Fine Particulates</span>
                    <span class="status-pill very-poor"><span class="pill-dot"></span>Primary Target</span>
                </div>
                <div class="metric-value-box">
                    <span class="metric-number">{pm25_val:.1f}</span>
                    <span class="metric-unit">µg/m³ PM2.5</span>
                </div>
                <div class="card-footer-meta">
                    <span style="color: #EF6461; font-weight: 600;">CPCB 24h Std: 60 µg/m³ ({pm25_mult:.1f}× limit)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k2:
        st.markdown(
            f"""
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Coarse Particulates</span>
                    <span class="status-pill poor"><span class="pill-dot"></span>PM10</span>
                </div>
                <div class="metric-value-box">
                    <span class="metric-number">{pm10_val:.1f}</span>
                    <span class="metric-unit">µg/m³ PM10</span>
                </div>
                <div class="card-footer-meta">
                    CPCB 24h Std: 100 µg/m³ • Inhalable mineral dust
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k3:
        if pd.notna(o3_val) and float(o3_val) > 0:
            o3_display = f"{float(o3_val):.1f}"
            o3_meta = "Photochemical secondary oxidant • 8h Std: 100 µg/m³"
            o3_pill = '<span class="status-pill good"><span class="pill-dot"></span>Measured</span>'
        else:
            o3_display = "N/A"
            o3_meta = "Sensor offline or nocturnal titration below detection"
            o3_pill = '<span class="status-pill" style="background:#F1F5F9; color:#64748B;"><span class="pill-dot"></span>Unavailable</span>'

        st.markdown(
            f"""
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Ground-Level Ozone</span>
                    {o3_pill}
                </div>
                <div class="metric-value-box">
                    <span class="metric-number">{o3_display}</span>
                    <span class="metric-unit">µg/m³ O3</span>
                </div>
                <div class="card-footer-meta">{o3_meta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Row 2: Weather & Forecast Horizons (Temperature, Wind Speed, Forecast Horizon)
    k4, k5, k6 = st.columns(3)
    with k4:
        st.markdown(
            f"""
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Ambient Temperature</span>
                    <span class="status-pill" style="background: #F1F5F9; color: #334155;"><span class="pill-dot"></span>Surface 2m</span>
                </div>
                <div class="metric-value-box">
                    <span class="metric-number">{temp_val:.1f}</span>
                    <span class="metric-unit">°C</span>
                </div>
                <div class="card-footer-meta">
                    Dew Point: {float(latest_obs.get('dew_point_2m', 0.0)):.1f}°C • RH: {rh_val:.0f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k5:
        is_stagnant = ws_val < 5.4
        ws_badge = '<span class="status-pill severe"><span class="pill-dot"></span>Stagnant</span>' if is_stagnant else '<span class="status-pill good"><span class="pill-dot"></span>Ventilating</span>'
        st.markdown(
            f"""
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">10m Wind Velocity</span>
                    {ws_badge}
                </div>
                <div class="metric-value-box">
                    <span class="metric-number">{ws_val:.1f}</span>
                    <span class="metric-unit">km/h ({ws_val / 3.6:.2f} m/s)</span>
                </div>
                <div class="card-footer-meta">
                    Dispersion Threshold: 1.5 m/s (5.4 km/h)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k6:
        st.markdown(
            """
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Forecasting Horizon</span>
                    <span class="status-pill good"><span class="pill-dot"></span>Active</span>
                </div>
                <div class="metric-value-box">
                    <span class="metric-number">72</span>
                    <span class="metric-unit">Hours Ahead</span>
                </div>
                <div class="card-footer-meta">
                    Direct Estimators: 24h, 48h, 72h • XGBoost Tier 2
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Interactive Delhi NCR Monitoring Network Map & Trend Chart Tabs
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.5rem;'>Spatial Monitoring & Temporal Evolution</div>",
        unsafe_allow_html=True,
    )

    tab_map, tab_trend = st.tabs(["Interactive Delhi NCR Monitoring Map", "7-Day Airshed Pollution Trend"])

    with tab_map:
        # Build interactive map across all stations
        map_records = []
        if df is not None and not df.empty:
            for s in all_stations:
                st_slice = df[df["station_id"] == s["id"]]
                if not st_slice.empty:
                    last_st = st_slice.iloc[-1]
                    st_pm25 = float(last_st.get("pm25", 0.0))
                    st_pm10 = float(last_st.get("pm10", 0.0))
                else:
                    st_pm25 = 0.0
                    st_pm10 = 0.0

                aqi_info = CPCBIndexCalculator.compute_official_aqi({"pm25": st_pm25, "pm10": st_pm10})
                sub_idx = aqi_info.get("aqi") or aqi_info.get("indicative_sub_index") or 0.0

                map_records.append({
                    "station_id": s["id"],
                    "name": s["name"],
                    "authority": s["authority"],
                    "city": s["city"],
                    "latitude": s["latitude"],
                    "longitude": s["longitude"],
                    "pm25": st_pm25,
                    "pm10": st_pm10,
                    "aqi": sub_idx,
                    "category": aqi_info["category"],
                    "color": aqi_info["color"],
                })

        map_df = pd.DataFrame(map_records)

        if not map_df.empty:
            fig_map = go.Figure()

            # Add station markers
            for cat, group in map_df.groupby("category"):
                color = group["color"].iloc[0]
                fig_map.add_trace(go.Scattermap(
                    lat=group["latitude"],
                    lon=group["longitude"],
                    mode="markers+text",
                    marker=dict(
                        size=group["pm25"].clip(lower=15, upper=55),
                        color=color,
                        opacity=0.88,
                    ),
                    text=group["name"],
                    textposition="top center",
                    textfont=dict(family="Plus Jakarta Sans, sans-serif", size=11, color="#172B4D"),
                    name=f"{cat} (AQI)",
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "Authority: %{customdata[1]} • %{customdata[2]}<br>"
                        "PM2.5: <b>%{customdata[3]:.1f} µg/m³</b><br>"
                        "PM10: %{customdata[4]:.1f} µg/m³<br>"
                        "CPCB NAQI: <b>%{customdata[5]:.0f} (%{customdata[6]})</b><extra></extra>"
                    ),
                    customdata=group[["name", "authority", "city", "pm25", "pm10", "aqi", "category"]].to_numpy(),
                ))

            fig_map.update_layout(
                map=dict(
                    style="open-street-map",
                    center=dict(lat=28.61, lon=77.20),
                    zoom=9.3,
                ),
                height=480,
                margin=dict(l=0, r=0, t=20, b=0),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=0.98,
                    xanchor="left",
                    x=0.01,
                    bgcolor="rgba(255, 255, 255, 0.9)",
                    bordercolor="#E2E8F0",
                    borderwidth=1,
                ),
            )
            st.plotly_chart(fig_map, use_container_width=True)
            st.caption("Point size reflects PM2.5 concentration; marker color indicates official statutory CPCB National Air Quality Index (NAQI) category.")

    with tab_trend:
        if df is not None and not df.empty:
            st_data = df[df["station_id"] == station["id"]].copy()
            if not st_data.empty:
                t_dates = pd.to_datetime(st_data["timestamp_ist"])
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=t_dates,
                    y=st_data["pm25"],
                    mode="lines",
                    name="PM2.5 (Fine Particulates)",
                    line=dict(color="#0D9488", width=2.5),
                    hovertemplate="Time: %{x}<br>PM2.5: <b>%{y:.1f} µg/m³</b><extra></extra>",
                ))
                fig_trend.add_hline(
                    y=60.0,
                    line_dash="dash",
                    line_color="#EF6461",
                    annotation_text="CPCB 24h Std (60 µg/m³)",
                    annotation_position="top right",
                )
                fig_trend = apply_custom_chart_theme(fig_trend, height=440, title=f"7-Day PM2.5 Time-Series — {station['name']}")
                st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    # Operational Forecast Availability & Station Matrix
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.6rem;'>Operational Forecast Horizons (Direct ML Architecture)</div>",
        unsafe_allow_html=True,
    )
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown(
            """
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Horizon H1</span>
                    <span class="status-pill good"><span class="pill-dot"></span>Ready</span>
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #0D9488; margin: 0.2rem 0;">t + 24 hrs</div>
                <div style="font-size: 0.76rem; color: #172B4D; font-weight: 600;">XGBoost Tier 2 Engine</div>
                <div class="card-footer-meta">Test RMSE: 48.28 µg/m³ • Direct</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f2:
        st.markdown(
            """
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Horizon H2</span>
                    <span class="status-pill good"><span class="pill-dot"></span>Ready</span>
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #0D9488; margin: 0.2rem 0;">t + 48 hrs</div>
                <div style="font-size: 0.76rem; color: #172B4D; font-weight: 600;">Coupled Meteorology Tier 2</div>
                <div class="card-footer-meta">Test RMSE: 54.19 µg/m³ • Direct</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f3:
        st.markdown(
            """
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Horizon H3</span>
                    <span class="status-pill good"><span class="pill-dot"></span>Ready</span>
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #0D9488; margin: 0.2rem 0;">t + 72 hrs</div>
                <div style="font-size: 0.76rem; color: #172B4D; font-weight: 600;">Synoptic Multi-Horizon</div>
                <div class="card-footer-meta">Test RMSE: 55.84 µg/m³ • Direct</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f4:
        st.markdown(
            """
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Attribution</span>
                    <span class="status-pill good"><span class="pill-dot"></span>Verified</span>
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #172B4D; margin: 0.2rem 0;">TreeSHAP XAI</div>
                <div style="font-size: 0.76rem; color: #172B4D; font-weight: 600;">Exact Game Theory</div>
                <div class="card-footer-meta">Zero approximation error</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # Monitored Station Network Grid
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin: 1rem 0 0.6rem;'>Monitored CAAQMS Sensor Network (Delhi NCR Airshed)</div>",
        unsafe_allow_html=True,
    )
    st_cols = st.columns(3)
    for idx, s in enumerate(all_stations):
        scol = st_cols[idx % 3]
        with scol:
            st.markdown(
                f"""
                <div class="atmos-card" style="margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #172B4D; font-size: 0.88rem;">{s['name']}</span>
                        <span style="font-family: 'JetBrains Mono', monospace; background: #F1F5F9; color: #334155; font-size: 0.68rem; font-weight: 600; padding: 0.15rem 0.45rem; border-radius: 4px;">{s['authority']}</span>
                    </div>
                    <p style="font-size: 0.78rem; color: #64748B; margin: 0.35rem 0;">{s['description']}</p>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #0D9488; font-weight: 600;">
                        📍 {s['latitude']:.4f}°N, {s['longitude']:.4f}°E ({s['city']})
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
