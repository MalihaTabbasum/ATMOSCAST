"""
Air Quality Monitoring View for AtmosCast.
"""

from typing import Any, Dict
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_air_quality_view(station: Dict[str, Any], station_df: pd.DataFrame):
    """
    Renders the Air Quality Monitoring page with interactive multi-pollutant charts.
    """
    st.markdown(
        f"""
        <div class="hero-header">
            <div class="hero-title">Air Quality Monitoring — {station['name']}</div>
            <div class="hero-subtitle">
                Continuous ground-level pollutant measurements from verified CAAQMS sensors • {station['authority']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Station Summary Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("PM2.5 (Mean)", f"{station_df['pm25'].mean():.1f} µg/m³", delta=f"{station_df['pm25'].max():.1f} max")
    with c2:
        st.metric("PM10 (Mean)", f"{station_df['pm10'].mean():.1f} µg/m³", delta=f"{station_df['pm10'].max():.1f} max")
    with c3:
        st.metric("NO2 (Mean)", f"{station_df['no2'].mean():.1f} µg/m³")
    with c4:
        st.metric("O3 (Mean)", f"{station_df['o3'].mean():.1f} µg/m³")

    st.markdown("---")

    # Time-Series Interactive Plotly Chart
    st.markdown("### Particulate Matter Concentrations (PM2.5 vs. PM10)")
    fig_pm = go.Figure()

    fig_pm.add_trace(go.Scatter(
        x=pd.to_datetime(station_df["timestamp_ist"]),
        y=station_df["pm25"],
        name="PM2.5 (Fine)",
        line=dict(color="#0D9488", width=2.5),
        hovertemplate="Time: %{x}<br>PM2.5: <b>%{y:.1f} µg/m³</b><extra></extra>",
    ))

    fig_pm.add_trace(go.Scatter(
        x=pd.to_datetime(station_df["timestamp_ist"]),
        y=station_df["pm10"],
        name="PM10 (Coarse)",
        line=dict(color="#F59E0B", width=2, dash="dot"),
        hovertemplate="Time: %{x}<br>PM10: <b>%{y:.1f} µg/m³</b><extra></extra>",
    ))

    # CPCB 24h Thresholds
    fig_pm.add_hline(y=60.0, line_dash="dash", line_color="#EF4444", annotation_text="CPCB 24h Limit (PM2.5: 60 µg/m³)")
    fig_pm.add_hline(y=100.0, line_dash="dash", line_color="#F97316", annotation_text="CPCB 24h Limit (PM10: 100 µg/m³)")

    fig_pm.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(family="Inter, sans-serif", color="#1E293B"),
        height=450,
        margin=dict(l=40, r=40, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig_pm.update_xaxes(title="Timestamp (IST)", gridcolor="#E2E8F0")
    fig_pm.update_yaxes(title="Concentration (µg/m³)", gridcolor="#E2E8F0")
    st.plotly_chart(fig_pm, use_container_width=True)

    # Secondary Pollutants & Photochemistry
    st.markdown("### Secondary Atmospheric Chemistry (NO2 vs. Ground-Level Ozone)")
    fig_gas = go.Figure()

    fig_gas.add_trace(go.Scatter(
        x=pd.to_datetime(station_df["timestamp_ist"]),
        y=station_df["no2"],
        name="NO2 (Nitrogen Dioxide)",
        line=dict(color="#3B82F6", width=2),
        hovertemplate="Time: %{x}<br>NO2: <b>%{y:.1f} µg/m³</b><extra></extra>",
    ))

    fig_gas.add_trace(go.Scatter(
        x=pd.to_datetime(station_df["timestamp_ist"]),
        y=station_df["o3"],
        name="O3 (Ground-Level Ozone)",
        line=dict(color="#10B981", width=2),
        hovertemplate="Time: %{x}<br>O3: <b>%{y:.1f} µg/m³</b><extra></extra>",
    ))

    fig_gas.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(family="Inter, sans-serif", color="#1E293B"),
        height=380,
        margin=dict(l=40, r=40, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig_gas.update_xaxes(title="Timestamp (IST)", gridcolor="#E2E8F0")
    fig_gas.update_yaxes(title="Concentration (µg/m³)", gridcolor="#E2E8F0")
    st.plotly_chart(fig_gas, use_container_width=True)
