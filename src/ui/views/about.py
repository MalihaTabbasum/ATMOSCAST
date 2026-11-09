"""
Data Sources and About View for AtmosCast.
"""

import streamlit as st


def render_about_view():
    """
    Renders the Data Sources, Provenance, and Project Governance documentation.
    """
    st.markdown(
        """
        <div class="hero-header">
            <div class="hero-title">Data Sources, Provenance & Architecture</div>
            <div class="hero-subtitle">
                Comprehensive data provenance, licensing, physical boundaries, and SIH Problem Statement SIH26082 details
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Core Data Sources Grid
    st.markdown("### Verified Real-World Data Ingestion Sources")

    s1, s2 = st.columns(2)
    with s1:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill good">Ground Observations</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43;">OpenAQ API v3</h4>
                <p style="font-size: 0.82rem; color: #64748B;">
                    Official ground-level CAAQMS measurements from CPCB, DPCC, HSPCB, and UPPCB stations across Delhi NCR.
                </p>
                <div style="font-size: 0.78rem; color: #0D9488; font-weight: 600;">
                    Parameters: PM2.5, PM10, NO2, O3, SO2, CO (µg/m³ & mg/m³)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill good">Surface Meteorology</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43;">Open-Meteo Historical Weather API</h4>
                <p style="font-size: 0.82rem; color: #64748B;">
                    High-resolution hourly surface meteorology aligned by geographic coordinates and UTC timestamps.
                </p>
                <div style="font-size: 0.78rem; color: #0D9488; font-weight: 600;">
                    Parameters: Temp (2m), RH, Dew Point, Surface Pressure, Wind Speed & Direction (10m)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s2:
        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill moderate">Satellite Fire Layer</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43;">NASA FIRMS (VIIRS & MODIS)</h4>
                <p style="font-size: 0.82rem; color: #64748B;">
                    Active thermal anomaly and Fire Radiative Power (FRP) tracking in the northwest agricultural stubble corridor.
                </p>
                <div style="font-size: 0.78rem; color: #0D9488; font-weight: 600;">
                    Status: Optional Source (Stubble-burning is minimal in January; local stagnation dominates)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="atmos-card">
                <span class="status-pill good">Atmospheric Composition</span>
                <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43;">Copernicus CAMS Reanalysis</h4>
                <p style="font-size: 0.82rem; color: #64748B;">
                    European Centre for Medium-Range Weather Forecasts (ECMWF) atmospheric chemistry reanalysis.
                </p>
                <div style="font-size: 0.78rem; color: #0D9488; font-weight: 600;">
                    Status: Verified Multi-Pollutant Benchmark
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Data Quality & Cleanliness Summary
    st.markdown("### Cleaned Analytical Dataset Specifications (Phase 3 Verified)")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.metric("Total Cleaned Records", "1,008 Rows", "168 hrs / station")
    with q2:
        st.metric("Monitoring Stations", "6 Stations", "Delhi, Noida, Gurugram")
    with q3:
        st.metric("Missing Value Rate", "0.00%", "Core parameters")
    with q4:
        st.metric("Temporal Resolution", "1 Hour", "Synchronized UTC & IST")

    st.markdown("---")

    # SIH Problem Statement & Scientific Disclaimer
    st.markdown("### Project Governance & Scientific Integrity Statement")
    st.markdown(
        """
        - **Problem Statement:** SIH26082 — Air Pollution–Weather Coupled Forecasting System (Delhi NCR Focus).
        - **Scientific Integrity Mandate:** AtmosCast does **NOT** falsely claim that a conventional machine learning model is a complete 3D coupled atmospheric physics and chemical transport simulator (e.g. WRF-Chem). Rather, AtmosCast is an empirical, weather-aware multi-horizon forecasting platform that bridges statistical machine learning, boundary-layer meteorology, and explainable AI.
        - **Licensing & Attribution:** Open-source release under MIT License. All data feeds are attributed to OpenAQ, Open-Meteo, ECMWF CAMS, and NASA EOSDIS.
        """
    )
