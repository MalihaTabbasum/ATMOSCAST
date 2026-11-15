"""
72-Hour Multi-Horizon Forecast View for AtmosCast.
"""

from typing import Any, Dict
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.forecasting.engine import ForecastEngine
from src.ui.theme import render_page_header, apply_custom_chart_theme


@st.cache_resource
def get_cached_engine():
    """Initializes and caches the ForecastEngine instance."""
    return ForecastEngine()


def render_forecast_view(station: Dict[str, Any], station_df: pd.DataFrame):
    """
    Renders the 72-Hour Forecast generation dashboard with interactive horizon filters,
    empirical uncertainty prediction bands, milestone projections, and CSV export.
    """
    render_page_header(
        kicker="DIRECT MULTI-HORIZON PROJECTION ENGINE",
        title=f"72-Hour Atmospheric Dispersion Forecast — {station['name']}",
        subtitle="Independent multi-horizon gradient boosted trees (XGBoost Tier 2) coupling antecedent pollution momentum with boundary-layer numerical weather prediction.",
    )

    engine = get_cached_engine()

    col_btn, col_info, col_dl = st.columns([1.2, 2.3, 1.2])
    with col_btn:
        generate_clicked = st.button("Run 72-Hour Forecast", use_container_width=True)

    with col_info:
        st.markdown(
            """
            <div style="font-size: 0.8rem; color: #64748B; padding-top: 0.4rem;">
                Direct horizon formulation (h ∈ {24, 48, 72}h) with zero recursive autoregressive error compounding.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Generate forecast
    with st.spinner("Executing 72-hour coupled atmospheric forecast..."):
        try:
            fc_result = engine.generate_72h_forecast(station_df, station_id=station["id"])
        except Exception as e:
            st.error(f"Error generating forecast: {str(e)}")
            return

    milestones = fc_result["milestone_predictions"]
    fc_df = fc_result["forecast_trajectory"].copy()
    hist_df = fc_result["historical_context"].copy()

    with col_dl:
        csv_forecast = fc_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Export Forecast (CSV)",
            data=csv_forecast,
            file_name=f"{station['id']}_72h_forecast_trajectory.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # Horizon Range Filter Control
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 0.95rem; font-weight: 700; color: #172B4D; margin: 0.8rem 0 0.3rem;'>Horizon Filter Selection</div>",
        unsafe_allow_html=True,
    )
    horizon_choice = st.radio(
        "Display Horizon Range:",
        ["Full 72-Hour Window", "24-Hour Horizon (t+1 to t+24)", "48-Hour Horizon (t+1 to t+48)", "72-Hour Horizon (t+1 to t+72)"],
        horizontal=True,
        label_visibility="collapsed",
    )

    max_h = 72
    if "24-Hour" in horizon_choice:
        max_h = 24
    elif "48-Hour" in horizon_choice:
        max_h = 48

    fc_df_filtered = fc_df[fc_df["horizon_hour"] <= max_h].copy()

    # Milestone KPI Cards
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin: 1rem 0 0.5rem;'>Key Horizon Lookahead Projections</div>",
        unsafe_allow_html=True,
    )
    m1, m2, m3 = st.columns(3)

    for col, h in zip([m1, m2, m3], [24, 48, 72]):
        row_h = fc_df[fc_df["horizon_hour"] == h].iloc[0]
        cat = row_h["aqi_category"]
        color = row_h["aqi_color"]
        val = row_h["predicted_pm25"]
        sub_idx = row_h["cpcb_sub_index"]

        with col:
            st.markdown(
                f"""
                <div class="atmos-card">
                    <div class="card-top-row">
                        <span class="card-label">Lookahead t + {h} Hours</span>
                        <span class="status-pill" style="background-color: {color}15; color: {color}; border: 1px solid {color}44;">
                            <span class="pill-dot" style="background-color: {color};"></span>
                            {cat}
                        </span>
                    </div>
                    <div class="metric-value-box">
                        <span class="metric-number">{val:.1f}</span>
                        <span class="metric-unit">µg/m³ PM2.5</span>
                    </div>
                    <div class="card-footer-meta">
                        Statutory AQI: <strong style="color: {color};">{sub_idx:.0f}</strong> • 90% PI: [{row_h['lower_bound_pm25']:.0f}, {row_h['upper_bound_pm25']:.0f}]
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Interactive 72-Hour Forecast Trajectory Chart
    st.markdown(
        f"<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.5rem;'>Continuous Trajectory ({max_h}h Forward) with Empirical 90% Prediction Interval</div>",
        unsafe_allow_html=True,
    )

    fig = go.Figure()

    # Historical Actual Observations (Past 24h)
    hist_dt = pd.to_datetime(hist_df["timestamp_utc"]).dt.tz_convert("Asia/Kolkata")
    fc_dt = pd.to_datetime(fc_df_filtered["timestamp_utc"]).dt.tz_convert("Asia/Kolkata")

    fig.add_trace(go.Scatter(
        x=hist_dt,
        y=hist_df["predicted_pm25"],
        mode="lines+markers",
        name="Observed History (Past 24h)",
        line=dict(color="#102A43", width=2.5),
        marker=dict(size=4, color="#102A43"),
        hovertemplate="Time: %{x}<br>Observed PM2.5: <b>%{y:.1f} µg/m³</b><extra></extra>",
    ))

    # Upper uncertainty bound
    fig.add_trace(go.Scatter(
        x=fc_dt,
        y=fc_df_filtered["upper_bound_pm25"],
        mode="lines",
        name="Upper 90% PI",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))

    # Lower uncertainty bound with shaded fill
    fig.add_trace(go.Scatter(
        x=fc_dt,
        y=fc_df_filtered["lower_bound_pm25"],
        mode="lines",
        name="90% Prediction Interval (±1.645×RMSE)",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(13, 148, 136, 0.12)",
        hovertemplate="Lower Bound: %{y:.1f} µg/m³<extra></extra>",
    ))

    # Forecast Trendline
    fig.add_trace(go.Scatter(
        x=fc_dt,
        y=fc_df_filtered["predicted_pm25"],
        mode="lines+markers",
        name=f"Forecast Projections (1 to {max_h}h)",
        line=dict(color="#0D9488", width=2.8, dash="solid"),
        marker=dict(size=4, color="#0D9488"),
        hovertemplate="Forecast Time: %{x}<br>Predicted PM2.5: <b>%{y:.1f} µg/m³</b><extra></extra>",
    ))

    # CPCB 24h Statutory Limit Line
    fig.add_hline(
        y=60.0,
        line_dash="dash",
        line_color="#EF6461",
        line_width=1.5,
        annotation_text="CPCB 24h Standard (60 µg/m³)",
        annotation_font=dict(family="JetBrains Mono, monospace", size=10, color="#EF6461"),
        annotation_position="top right",
    )

    fig.update_xaxes(title="Observation & Projection Timestamp (IST)")
    fig.update_yaxes(title="PM2.5 Concentration (µg/m³)")
    fig = apply_custom_chart_theme(fig, height=460)

    st.plotly_chart(fig, use_container_width=True)

    # Forecast Provenance Metadata Strip
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.75rem 1.15rem; font-size: 0.76rem; color: #64748B; box-shadow: 0 1px 2px rgba(15,23,42,0.03);">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.75rem;">
                <div><span style="font-weight: 700; color: #172B4D;">Model Version:</span> v1.0.0 (Atmospheric Tier 2)</div>
                <div><span style="font-weight: 700; color: #172B4D;">Model Family:</span> {fc_result['model_architecture']}</div>
                <div><span style="font-weight: 700; color: #172B4D;">Forecast Execution IST:</span> {fc_result['forecast_generated_at_ist']}</div>
                <div><span style="font-weight: 700; color: #172B4D;">Uncertainty Calibration:</span> Empirical Gaussian (±1.645×RMSE)</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Granular Hourly Data Table View
    with st.expander(f"Tabular Hourly Forecast Records (1 to {max_h} Hours)"):
        display_cols = ["horizon_hour", "timestamp_ist", "predicted_pm25", "lower_bound_pm25", "upper_bound_pm25", "predicted_pm10", "cpcb_sub_index", "aqi_category"]
        table_df = fc_df_filtered[display_cols].copy()
        table_df.columns = ["Horizon (h)", "Timestamp (IST)", "Pred PM2.5 (µg/m³)", "Lower Bound", "Upper Bound", "Pred PM10", "Statutory AQI", "Category"]
        st.dataframe(table_df, use_container_width=True)
