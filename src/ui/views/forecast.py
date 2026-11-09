"""
72-Hour Multi-Horizon Forecast View for AtmosCast.
"""

from typing import Any, Dict
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.forecasting.engine import ForecastEngine


@st.cache_resource
def get_cached_engine():
    """Initializes and caches the ForecastEngine instance."""
    return ForecastEngine()


def render_forecast_view(station: Dict[str, Any], station_df: pd.DataFrame):
    """
    Renders the 72-Hour Forecast generation dashboard.
    """
    st.markdown(
        f"""
        <div class="hero-header">
            <div class="hero-title">72-Hour Air Quality Forecast — {station['name']}</div>
            <div class="hero-subtitle">
                Direct multi-horizon predictions coupled with surface meteorology and atmospheric stability
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    engine = get_cached_engine()

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        generate_clicked = st.button("🚀 Generate 72-Hour Forecast", use_container_width=True)

    with col_info:
        st.caption("Forecasts are generated using trained gradient boosted tree models (XGBoost Tier 2) with direct horizon formulations.")

    # Generate forecast
    with st.spinner("Generating 72-hour coupled forecast..."):
        try:
            fc_result = engine.generate_72h_forecast(station_df, station_id=station["id"])
        except Exception as e:
            st.error(f"Error generating forecast: {str(e)}")
            return

    milestones = fc_result["milestone_predictions"]
    fc_df = fc_result["forecast_trajectory"]
    hist_df = fc_result["historical_context"]

    # Milestone KPI Cards
    st.markdown("### Milestone Lookahead Projections")
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
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; color: #102A43;">t + {h} Hours</span>
                        <span class="status-pill" style="background-color: {color}22; color: {color}; border: 1px solid {color}66;">
                            {cat}
                        </span>
                    </div>
                    <div class="metric-value-box" style="margin-top: 0.5rem;">
                        <span class="metric-number" style="color: #102A43;">{val:.1f}</span>
                        <span class="metric-unit">µg/m³ PM2.5</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B;">
                        Statutory AQI: <strong style="color: {color};">{sub_idx:.0f}</strong> • Bounds: {row_h['lower_bound_pm25']:.0f} - {row_h['upper_bound_pm25']:.0f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Interactive 72-Hour Forecast Trajectory Chart
    st.markdown("### 72-Hour Continuous Forecast Trajectory with 90% Uncertainty Envelope")

    fig = go.Figure()

    # Historical Actual Observations (Past 24h)
    hist_dt = pd.to_datetime(hist_df["timestamp_utc"]).dt.tz_convert("Asia/Kolkata")
    fc_dt = pd.to_datetime(fc_df["timestamp_utc"]).dt.tz_convert("Asia/Kolkata")

    fig.add_trace(go.Scatter(
        x=hist_dt,
        y=hist_df["predicted_pm25"],
        mode="lines+markers",
        name="Observed History",
        line=dict(color="#102A43", width=3),
        marker=dict(size=5),
        hovertemplate="Observed Time: %{x}<br>Actual PM2.5: <b>%{y:.1f} µg/m³</b><extra></extra>",
    ))

    # Upper uncertainty bound
    fig.add_trace(go.Scatter(
        x=fc_dt,
        y=fc_df["upper_bound_pm25"],
        mode="lines",
        name="Upper 90% PI",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))

    # Lower uncertainty bound with shaded fill
    fig.add_trace(go.Scatter(
        x=fc_dt,
        y=fc_df["lower_bound_pm25"],
        mode="lines",
        name="90% Prediction Interval",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(13, 148, 136, 0.15)",
        hovertemplate="Lower Bound: %{y:.1f} µg/m³<extra></extra>",
    ))

    # Forecast Trendline
    fig.add_trace(go.Scatter(
        x=fc_dt,
        y=fc_df["predicted_pm25"],
        mode="lines+markers",
        name="72h Forecast",
        line=dict(color="#0D9488", width=3),
        marker=dict(size=4),
        hovertemplate="Forecast Time: %{x}<br>Predicted PM2.5: <b>%{y:.1f} µg/m³</b><extra></extra>",
    ))

    # CPCB 24h Statutory Limit Line
    fig.add_hline(y=60.0, line_dash="dash", line_color="#EF4444", annotation_text="CPCB 24h Standard (60 µg/m³)")

    fig.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(family="Inter, sans-serif", color="#1E293B"),
        height=480,
        margin=dict(l=40, r=40, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title="Timestamp (IST)", gridcolor="#E2E8F0")
    fig.update_yaxes(title="PM2.5 Concentration (µg/m³)", gridcolor="#E2E8F0")

    st.plotly_chart(fig, use_container_width=True)

    # Forecast Provenance Metadata Card
    st.markdown(
        f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.85rem 1.25rem; font-size: 0.8rem; color: #64748B;">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
                <div><strong>Model Architecture:</strong> {fc_result['model_architecture']}</div>
                <div><strong>Generated:</strong> {fc_result['forecast_generated_at_ist']}</div>
                <div><strong>Weather Source:</strong> {fc_result['weather_source']}</div>
                <div><strong>Demonstration Mode:</strong> {'Yes (Historical Fallback)' if fc_result['is_fallback'] else 'Live NWP'}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Data Table View
    with st.expander("📋 View Complete 72-Hour Forecast Data Table"):
        display_cols = ["horizon_hour", "timestamp_ist", "predicted_pm25", "lower_bound_pm25", "upper_bound_pm25", "predicted_pm10", "cpcb_sub_index", "aqi_category"]
        table_df = fc_df[display_cols].copy()
        table_df.columns = ["Horizon (h)", "Timestamp (IST)", "Pred PM2.5 (µg/m³)", "Lower Bound", "Upper Bound", "Pred PM10", "Statutory AQI", "Category"]
        st.dataframe(table_df, use_container_width=True)
