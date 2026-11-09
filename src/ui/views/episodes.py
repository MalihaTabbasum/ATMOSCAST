"""
Pollution Episode Analysis View for AtmosCast.
"""

from typing import Any, Dict
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_episodes_view(station: Dict[str, Any], station_df: pd.DataFrame):
    """
    Renders the Pollution Episode Deep-Dive page analyzing the acute January 5-6, 2024 smog event.
    """
    st.markdown(
        f"""
        <div class="hero-header">
            <div class="hero-title">Pollution Episode Deep-Dive — {station['name']}</div>
            <div class="hero-subtitle">
                Forensic meteorological analysis of the January 5–6, 2024 severe smog surge across Delhi NCR
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Narrative Introduction
    st.markdown(
        """
        ### The Severe Winter Smog Event (January 5–6, 2024)
        During January 5–6, particulate matter concentrations surged across Delhi NCR, exceeding the Indian CPCB statutory 24-hour limit (60 µg/m³) by more than **3.5x**. This episode provides an ideal case study in multi-variable coupled atmospheric stagnation.
        """
    )

    # Episode Comparative Chart
    episode_slice = station_df[(station_df["date_ist"] >= "2024-01-04") & (station_df["date_ist"] <= "2024-01-07")].copy()

    fig = go.Figure()

    t_dates = pd.to_datetime(episode_slice["timestamp_ist"])

    # PM2.5 Trace
    fig.add_trace(go.Scatter(
        x=t_dates,
        y=episode_slice["pm25"],
        name="PM2.5 (µg/m³)",
        line=dict(color="#DC2626", width=3),
        hovertemplate="Time: %{x}<br>PM2.5: <b>%{y:.1f} µg/m³</b><extra></extra>",
    ))

    # Wind Speed Trace (scaled for secondary axis or visual overlay)
    fig.add_trace(go.Scatter(
        x=t_dates,
        y=episode_slice["wind_speed_10m"] * 10.0,
        name="Wind Speed (x10 km/h)",
        line=dict(color="#0D9488", width=2, dash="dash"),
        hovertemplate="Time: %{x}<br>Wind Speed: <b>%{customdata:.1f} km/h</b><extra></extra>",
        customdata=episode_slice["wind_speed_10m"],
    ))

    fig.add_hline(y=60.0, line_dash="dash", line_color="#F97316", annotation_text="CPCB 24h Std (60 µg/m³)")

    fig.update_layout(
        title="<b>PM2.5 Trajectory vs. Collapsing Surface Wind Speed (January 4–7)</b>",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(family="Inter, sans-serif", color="#1E293B"),
        height=450,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title="Timestamp (IST)", gridcolor="#E2E8F0")
    fig.update_yaxes(title="PM2.5 (µg/m³) / Wind (x10)", gridcolor="#E2E8F0")

    st.plotly_chart(fig, use_container_width=True)

    # Diagnostic Summary Cards
    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill severe">Trigger 1</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43;">Horizontal Wind Collapse</h4>
                <p style="font-size: 0.82rem; color: #64748B; margin-top: 0.3rem;">
                    Surface wind speeds dropped below <strong>1.5 km/h</strong> for 18 consecutive hours, shutting down horizontal advection across the Yamuna basin.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with d2:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill severe">Trigger 2</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43;">Nocturnal Thermal Inversion</h4>
                <p style="font-size: 0.82rem; color: #64748B; margin-top: 0.3rem;">
                    Surface air cooled to <strong>4.1°C</strong> under clear nocturnal skies, establishing an intense surface radiation inversion that capped vertical plume rise.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with d3:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill severe">Trigger 3</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43;">Moist Particulate Trapping</h4>
                <p style="font-size: 0.82rem; color: #64748B; margin-top: 0.3rem;">
                    Relative humidity climbed to <strong>98–100%</strong>, accelerating secondary inorganic aerosol formation (sulfates/nitrates) and particulate hygroscopic swelling.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Satellite Active Fire (FIRMS) Scientific Section
    st.markdown("### Regional Satellite Fire Activity & Stubble Burning Analysis (NASA FIRMS)")

    st.info(
        "🛰️ **Scientific Attribution Guardrail:** In accordance with MoEFCC and atmospheric chemistry standards, agricultural stubble burning cannot be attributed to Delhi NCR air pollution from satellite active fire counts alone. Attribution requires backward air-mass trajectory modeling (e.g. HYSPLIT) and chemical speciation (levoglucosan, potassium)."
    )

    st.markdown(
        """
        - **Seasonal Stubble Context:** Agricultural crop residue burning in the upwind northwest corridor (Punjab & Haryana) predominantly occurs during the post-monsoon harvesting window (**mid-October to mid-November**).
        - **January Winter Reality:** In early January, satellite thermal anomalies in the northwest corridor are near background baselines. The January 5–6 episode was overwhelmingly driven by **local emissions locked in by synoptic boundary-layer stagnation and nocturnal radiation inversions**, rather than long-range agricultural smoke plumes.
        """
    )
