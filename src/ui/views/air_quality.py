"""
Air Quality Monitoring View for AtmosCast.
"""

from typing import Any, Dict
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.theme import render_page_header, apply_custom_chart_theme


def render_air_quality_view(station: Dict[str, Any], station_df: pd.DataFrame):
    """
    Renders the Air Quality Monitoring page with interactive multi-pollutant charts,
    date-range filtering, 24h rolling averages, diurnal analysis, and CSV export.
    """
    render_page_header(
        kicker="GROUND SENSOR TELEMETRY & TREND SURVEILLANCE",
        title=f"Air Quality Surveillance — {station['name']}",
        subtitle=f"Continuous ground-level pollutant concentrations from verified {station['authority']} CAAQMS instrumentation across hourly reporting windows.",
    )

    # Date-Range Filtering Controls & Export Header
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 0.95rem; font-weight: 700; color: #172B4D; margin-bottom: 0.4rem;'>Temporal Filter & Data Controls</div>",
        unsafe_allow_html=True,
    )

    station_df = station_df.copy()
    station_df["dt_ist"] = pd.to_datetime(station_df["timestamp_ist"])
    min_date = station_df["dt_ist"].dt.date.min()
    max_date = station_df["dt_ist"].dt.date.max()

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.5, 1.5, 1.2])
    with ctrl_col1:
        start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
    with ctrl_col2:
        end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

    # Filter dataframe
    mask = (station_df["dt_ist"].dt.date >= start_date) & (station_df["dt_ist"].dt.date <= end_date)
    filtered_df = station_df.loc[mask].copy()

    if filtered_df.empty:
        st.warning("No sensor records match the selected date window. Resetting to full range.")
        filtered_df = station_df.copy()

    with ctrl_col3:
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Data (CSV)",
            data=csv_data,
            file_name=f"{station['id']}_air_quality_observations.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # Filtered Summary Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            "PM2.5 Mean (Filtered)",
            f"{filtered_df['pm25'].mean():.1f} µg/m³",
            delta=f"Max: {filtered_df['pm25'].max():.1f} µg/m³",
            delta_color="inverse",
        )
    with c2:
        st.metric(
            "PM10 Mean (Filtered)",
            f"{filtered_df['pm10'].mean():.1f} µg/m³",
            delta=f"Max: {filtered_df['pm10'].max():.1f} µg/m³",
            delta_color="inverse",
        )
    with c3:
        st.metric(
            "NO2 Mean (Filtered)",
            f"{filtered_df['no2'].mean():.1f} µg/m³",
            delta=f"Max: {filtered_df['no2'].max():.1f} µg/m³",
            delta_color="inverse",
        )
    with c4:
        o3_mean = filtered_df['o3'].dropna().mean() if 'o3' in filtered_df else 0.0
        o3_max = filtered_df['o3'].dropna().max() if 'o3' in filtered_df else 0.0
        st.metric(
            "O3 Mean (Filtered)",
            f"{o3_mean:.1f} µg/m³",
            delta=f"Max: {o3_max:.1f} µg/m³",
            delta_color="off",
        )

    st.markdown("---")

    # Multi-tab view: Time-series, 24h Rolling Averages, Diurnal Cycles
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.5rem;'>Interactive Air Quality Time-Series & Diurnal Analysis</div>",
        unsafe_allow_html=True,
    )

    t1, t2, t3 = st.tabs(["Hourly Concentrations", "24-Hour Rolling Averages", "Diurnal Cycle Profile"])

    with t1:
        fig_pm = go.Figure()
        fig_pm.add_trace(go.Scatter(
            x=filtered_df["dt_ist"],
            y=filtered_df["pm25"],
            name="PM2.5 (Fine Particulates)",
            line=dict(color="#0D9488", width=2.5),
            hovertemplate="Time (IST): %{x}<br>PM2.5: <b>%{y:.1f} µg/m³</b><extra></extra>",
        ))
        fig_pm.add_trace(go.Scatter(
            x=filtered_df["dt_ist"],
            y=filtered_df["pm10"],
            name="PM10 (Inhalable Coarse)",
            line=dict(color="#D97706", width=2, dash="dot"),
            hovertemplate="Time (IST): %{x}<br>PM10: <b>%{y:.1f} µg/m³</b><extra></extra>",
        ))

        # CPCB 24h Thresholds
        fig_pm.add_hline(
            y=60.0,
            line_dash="dash",
            line_color="#EF6461",
            line_width=1.5,
            annotation_text="CPCB 24h Limit (PM2.5: 60 µg/m³)",
            annotation_font=dict(family="JetBrains Mono, monospace", size=10, color="#EF6461"),
            annotation_position="top right",
        )
        fig_pm.add_hline(
            y=100.0,
            line_dash="dash",
            line_color="#F59E0B",
            line_width=1.5,
            annotation_text="CPCB 24h Limit (PM10: 100 µg/m³)",
            annotation_font=dict(family="JetBrains Mono, monospace", size=10, color="#F59E0B"),
            annotation_position="bottom right",
        )

        fig_pm.update_xaxes(title="Observation Timestamp (IST)")
        fig_pm.update_yaxes(title="Concentration (µg/m³)")
        fig_pm = apply_custom_chart_theme(fig_pm, height=440, title="Hourly Particulate Concentrations vs Statutory Standards")
        st.plotly_chart(fig_pm, use_container_width=True)

    with t2:
        # Compute rolling averages
        filtered_df["pm25_roll24"] = filtered_df["pm25"].rolling(window=24, min_periods=1).mean()
        filtered_df["pm10_roll24"] = filtered_df["pm10"].rolling(window=24, min_periods=1).mean()

        fig_roll = go.Figure()
        fig_roll.add_trace(go.Scatter(
            x=filtered_df["dt_ist"],
            y=filtered_df["pm25_roll24"],
            name="PM2.5 24h Rolling Mean",
            line=dict(color="#0D9488", width=3),
            hovertemplate="Time: %{x}<br>24h Rolling PM2.5: <b>%{y:.1f} µg/m³</b><extra></extra>",
        ))
        fig_roll.add_trace(go.Scatter(
            x=filtered_df["dt_ist"],
            y=filtered_df["pm10_roll24"],
            name="PM10 24h Rolling Mean",
            line=dict(color="#D97706", width=2.5, dash="dash"),
            hovertemplate="Time: %{x}<br>24h Rolling PM10: <b>%{y:.1f} µg/m³</b><extra></extra>",
        ))
        fig_roll.add_hline(
            y=60.0,
            line_dash="dash",
            line_color="#EF6461",
            annotation_text="Statutory CPCB 24h Threshold (60 µg/m³)",
            annotation_position="top right",
        )
        fig_roll.update_xaxes(title="Observation Timestamp (IST)")
        fig_roll.update_yaxes(title="24-Hour Rolling Mean (µg/m³)")
        fig_roll = apply_custom_chart_theme(fig_roll, height=440, title="24-Hour Rolling Smoothing (Baseline Trend)")
        st.plotly_chart(fig_roll, use_container_width=True)

    with t3:
        # Diurnal profile by hour of day (0 to 23)
        diurnal = station_df.groupby("hour_ist")[["pm25", "pm10", "no2"]].mean().reset_index()
        fig_diurnal = go.Figure()
        fig_diurnal.add_trace(go.Scatter(
            x=diurnal["hour_ist"],
            y=diurnal["pm25"],
            mode="lines+markers",
            name="PM2.5 Diurnal Mean",
            line=dict(color="#0D9488", width=2.5),
            marker=dict(size=6),
            hovertemplate="Hour %{x}:00 IST<br>Mean PM2.5: <b>%{y:.1f} µg/m³</b><extra></extra>",
        ))
        fig_diurnal.add_trace(go.Scatter(
            x=diurnal["hour_ist"],
            y=diurnal["pm10"],
            mode="lines+markers",
            name="PM10 Diurnal Mean",
            line=dict(color="#D97706", width=2, dash="dot"),
            marker=dict(size=6),
            hovertemplate="Hour %{x}:00 IST<br>Mean PM10: <b>%{y:.1f} µg/m³</b><extra></extra>",
        ))
        fig_diurnal.update_xaxes(title="Hour of Day (IST)", tickmode="linear", tick0=0, dtick=2)
        fig_diurnal.update_yaxes(title="Mean Concentration (µg/m³)")
        fig_diurnal = apply_custom_chart_theme(fig_diurnal, height=440, title="Diurnal Inversion Cycles (Morning Rush vs Nocturnal Stagnation)")
        st.plotly_chart(fig_diurnal, use_container_width=True)

    # Scientific Diagnostics: PM2.5 / PM10 Ratio
    pm_ratio = (filtered_df["pm25"] / filtered_df["pm10"].replace(0, float("nan"))).dropna()
    mean_ratio = pm_ratio.mean()

    st.markdown(
        f"""
        <div class="intel-brief">
            <div class="intel-brief-title">
                Diagnostic Atmospheric Chemistry: PM2.5 / PM10 Ratio = <strong>{mean_ratio:.2f}</strong>
            </div>
            <p class="intel-brief-body">
                The observed ratio of <strong>{mean_ratio:.2f}</strong> significantly exceeds the typical mineral dust baseline (~0.35–0.45). Ratios above 0.60 indicate that the airshed aerosol burden is heavily dominated by <strong>fine combustion byproducts and secondary particulate formation</strong> (sulfates and nitrates) rather than coarse resuspended mechanical crustal dust.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Secondary Pollutants & Photochemistry
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.5rem;'>Secondary Photochemistry: Nitrogen Dioxide (NO2) vs. Ground-Level Ozone (O3)</div>",
        unsafe_allow_html=True,
    )
    fig_gas = go.Figure()

    fig_gas.add_trace(go.Scatter(
        x=filtered_df["dt_ist"],
        y=filtered_df["no2"],
        name="NO2 (Primary Vehicle/Industrial Precursor)",
        line=dict(color="#2563EB", width=2),
        hovertemplate="Time (IST): %{x}<br>NO2: <b>%{y:.1f} µg/m³</b><extra></extra>",
    ))

    if "o3" in filtered_df and filtered_df["o3"].notna().sum() > 0:
        fig_gas.add_trace(go.Scatter(
            x=filtered_df["dt_ist"],
            y=filtered_df["o3"],
            name="O3 (Photochemical Secondary Product)",
            line=dict(color="#10B981", width=2),
            hovertemplate="Time (IST): %{x}<br>O3: <b>%{y:.1f} µg/m³</b><extra></extra>",
        ))

    fig_gas.update_xaxes(title="Observation Timestamp (IST)")
    fig_gas.update_yaxes(title="Concentration (µg/m³)")
    fig_gas = apply_custom_chart_theme(fig_gas, height=380)
    st.plotly_chart(fig_gas, use_container_width=True)
