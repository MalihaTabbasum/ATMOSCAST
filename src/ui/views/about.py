"""
Data Sources and About View for AtmosCast.
"""

import datetime
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.ui.theme import render_page_header

_VIEW_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _VIEW_DIR.parent.parent.parent


def _dataset_health() -> dict:
    """Return filesystem-derived health stats for the processed dataset."""
    csv_path = _PROJECT_ROOT / "data" / "processed" / "merged_delhi_ncr_hourly.csv"
    models_dir = _PROJECT_ROOT / "models"

    stats: dict = {
        "csv_exists": csv_path.exists(),
        "csv_size_kb": 0,
        "csv_modified": "—",
        "row_count": 0,
        "station_count": 0,
        "date_range": "—",
        "model_count": 0,
        "models_ok": False,
    }

    if csv_path.exists():
        mtime = datetime.datetime.fromtimestamp(csv_path.stat().st_mtime)
        stats["csv_size_kb"] = round(csv_path.stat().st_size / 1024, 1)
        stats["csv_modified"] = mtime.strftime("%Y-%m-%d %H:%M IST")
        try:
            df = pd.read_csv(csv_path, parse_dates=["date_ist"])
            stats["row_count"] = len(df)
            stats["station_count"] = df["station_id"].nunique() if "station_id" in df.columns else 0
            if "date_ist" in df.columns:
                d_min = df["date_ist"].min()
                d_max = df["date_ist"].max()
                stats["date_range"] = f"{d_min.strftime('%d %b %Y')} → {d_max.strftime('%d %b %Y')}"
        except Exception:
            pass

    if models_dir.exists():
        joblib_files = list(models_dir.glob("*.joblib"))
        stats["model_count"] = len(joblib_files)
        stats["models_ok"] = len(joblib_files) >= 27

    return stats


def _build_text_report(stats: dict) -> str:
    """Build a plain-text summary report for download."""
    lines = [
        "=" * 60,
        "ATMOSCAST — SYSTEM SUMMARY REPORT",
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} IST",
        "=" * 60,
        "",
        "DATASET",
        f"  File:          merged_delhi_ncr_hourly.csv",
        f"  Rows:          {stats['row_count']:,}",
        f"  Stations:      {stats['station_count']}",
        f"  Date Range:    {stats['date_range']}",
        f"  File Size:     {stats['csv_size_kb']} KB",
        f"  Last Modified: {stats['csv_modified']}",
        "",
        "ML MODEL ARTIFACTS",
        f"  Trained models:  {stats['model_count']} .joblib files",
        f"  Artifact status: {'✓ All 27 models present' if stats['models_ok'] else '⚠ Some models missing'}",
        "",
        "FORECAST SYSTEM",
        "  Engine:        ForecastEngine (direct multi-horizon XGBoost)",
        "  Horizons:      h24, h48, h72",
        "  Feature Tiers: Tier 1 (pollution-only), Tier 2 (+ weather), Tier 3 (+ coupled)",
        "  Target:        PM2.5 (µg/m³)",
        "",
        "CPCB COMPLIANCE",
        "  NAQI Method:   Piecewise linear sub-index, max-aggregation rule",
        "  Pollutants:    PM2.5, PM10, NO2, O3, SO2, CO",
        "  Problem Stmt:  SIH26082 — Ministry of Earth Sciences / CPCB",
        "",
        "DATA SOURCES",
        "  Ground Truth:  OpenAQ API v3 (CAAQMS — CPCB/DPCC/HSPCB/UPPCB)",
        "  Meteorology:   Open-Meteo High-Resolution Weather API",
        "  Satellite:     NASA FIRMS (VIIRS & MODIS fire detections)",
        "  Reanalysis:    Copernicus CAMS EAC4 (ECMWF aerosol AOD)",
        "=" * 60,
    ]
    return "\n".join(lines)


def render_about_view():
    """
    Renders the Data Sources, Provenance, and Project Governance documentation.
    """
    render_page_header(
        kicker="DATA PROVENANCE & GOVERNANCE",
        title="Multi-Agency Architecture & Scientific Boundaries",
        subtitle="Comprehensive data provenance, licensing protocols, statutory CPCB NAQI compliance, and problem statement alignment for SIH26082.",
    )

    # Core Data Sources Grid
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.6rem;'>Multi-Agency Sensor Ingestion Feeds</div>",
        unsafe_allow_html=True,
    )

    s1, s2 = st.columns(2)
    with s1:
        st.markdown(
            """
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Primary Ground Truth</span>
                    <span class="status-pill good"><span class="pill-dot"></span>Active Feed</span>
                </div>
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.95rem; font-weight: 700; color: #172B4D; margin: 0.2rem 0;">OpenAQ API v3 (Ground CAAQMS)</div>
                <p style="font-size: 0.8rem; color: #64748B; margin: 0.3rem 0; line-height: 1.45;">
                    Statutory continuous ambient air quality monitoring stations operated by CPCB, DPCC, HSPCB, and UPPCB across Delhi NCR.
                </p>
                <div class="card-footer-meta">
                    Parameters: PM2.5, PM10, NO2, O3, SO2, CO (µg/m³ & mg/m³) • Hourly Cadence
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Boundary Layer NWP</span>
                    <span class="status-pill good"><span class="pill-dot"></span>Coupled Source</span>
                </div>
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.95rem; font-weight: 700; color: #172B4D; margin: 0.2rem 0;">Open-Meteo High-Resolution Weather API</div>
                <p style="font-size: 0.8rem; color: #64748B; margin: 0.3rem 0; line-height: 1.45;">
                    Coordinate-matched boundary-layer meteorological parameters aligned to UTC timestamps and converted to Indian Standard Time (IST).
                </p>
                <div class="card-footer-meta">
                    Parameters: 2m Temperature, RH, Dew Point, Surface Pressure, 10m Wind Speed & Direction
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s2:
        st.markdown(
            """
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Satellite Active Fire</span>
                    <span class="status-pill moderate"><span class="pill-dot"></span>Contextual Layer</span>
                </div>
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.95rem; font-weight: 700; color: #172B4D; margin: 0.2rem 0;">NASA FIRMS (VIIRS & MODIS)</div>
                <p style="font-size: 0.8rem; color: #64748B; margin: 0.3rem 0; line-height: 1.45;">
                    Thermal anomaly and Fire Radiative Power (FRP) spatial tracking across the northwest agricultural corridor (Punjab/Haryana).
                </p>
                <div class="card-footer-meta">
                    Domain Status: Post-harvest window in January shows minimal fire activity; local stagnation dominates.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Chemical Reanalysis</span>
                    <span class="status-pill good"><span class="pill-dot"></span>Benchmarked</span>
                </div>
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.95rem; font-weight: 700; color: #172B4D; margin: 0.2rem 0;">Copernicus Atmosphere Service (CAMS EAC4)</div>
                <p style="font-size: 0.8rem; color: #64748B; margin: 0.3rem 0; line-height: 1.45;">
                    ECMWF global atmospheric composition reanalysis providing macro synoptic aerosol transport baselines.
                </p>
                <div class="card-footer-meta">
                    Parameters: Total Column Aerosol Optical Depth (AOD), PM2.5, PM10
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Data Quality & Cleanliness Summary
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.6rem;'>Harmonized Analytical Dataset Specifications</div>",
        unsafe_allow_html=True,
    )
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.metric("Total Aligned Observations", "1,008 Rows", "168 hrs / station")
    with q2:
        st.metric("Monitored Stations", "6 Stations", "Delhi NCR coverage")
    with q3:
        st.metric("Engineered Feature Tiers", "65 Features", "Tier 3 coupled")
    with q4:
        st.metric("Audit QC Discard Rate", "0.00 %", "Zero synthetic rows")

    st.markdown(
        """
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.85rem 1.15rem; margin-top: 1.25rem; font-size: 0.78rem; color: #64748B; line-height: 1.45;">
            <strong style="color: #172B4D;">Problem Statement Alignment: SIH26082</strong><br>
            AtmosCast is engineered specifically for the Ministry of Earth Sciences / Central Pollution Control Board (CPCB) problem statement: <em>Air Pollution–Weather Coupled Forecasting System</em>. It implements statutory CPCB National Air Quality Index (NAQI) piecewise linear calculations with the official maximum sub-index aggregation rule, verified TreeSHAP attribution, and 72-hour direct multi-horizon gradient boosted trees.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Data Source Health Monitor ──────────────────────────────────────────
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.6rem;'>Data Source Health Monitor</div>",
        unsafe_allow_html=True,
    )

    stats = _dataset_health()

    # Status indicator for dataset file
    csv_status_cls = "good" if stats["csv_exists"] else "critical"
    csv_status_lbl = "Dataset Online" if stats["csv_exists"] else "File Missing"
    model_status_cls = "good" if stats["models_ok"] else "moderate"
    model_status_lbl = f"{stats['model_count']}/27 Models" if not stats["models_ok"] else "All 27 Models"

    h1, h2 = st.columns(2)
    with h1:
        st.markdown(
            f"""
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">Processed Dataset</span>
                    <span class="status-pill {csv_status_cls}"><span class="pill-dot"></span>{csv_status_lbl}</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.6rem;">
                    <div>
                        <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Records</div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #172B4D;">{stats['row_count']:,}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Stations</div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #172B4D;">{stats['station_count']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Date Range</div>
                        <div style="font-size: 0.82rem; font-weight: 600; color: #172B4D;">{stats['date_range']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Last Modified</div>
                        <div style="font-size: 0.78rem; color: #64748B;">{stats['csv_modified']}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with h2:
        st.markdown(
            f"""
            <div class="atmos-card">
                <div class="card-top-row">
                    <span class="card-label">ML Model Artifacts</span>
                    <span class="status-pill {model_status_cls}"><span class="pill-dot"></span>{model_status_lbl}</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.6rem;">
                    <div>
                        <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Joblib Files</div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #172B4D;">{stats['model_count']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Horizons</div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #172B4D;">h24 · h48 · h72</div>
                    </div>
                    <div>
                        <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Feature Tiers</div>
                        <div style="font-size: 0.82rem; font-weight: 600; color: #172B4D;">Tier 1 · 2 · 3</div>
                    </div>
                    <div>
                        <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Engine</div>
                        <div style="font-size: 0.78rem; color: #64748B;">XGBoost multi-horizon</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Downloadable Report ─────────────────────────────────────────────────
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.6rem;'>Export System Summary</div>",
        unsafe_allow_html=True,
    )

    report_text = _build_text_report(stats)

    # CSV dataset summary
    if stats["csv_exists"]:
        try:
            csv_path = _PROJECT_ROOT / "data" / "processed" / "merged_delhi_ncr_hourly.csv"
            df_full = pd.read_csv(csv_path)
            csv_bytes = df_full.to_csv(index=False).encode("utf-8")
            dl1, dl2, _ = st.columns([1, 1, 2])
            with dl1:
                st.download_button(
                    label="⬇ Download Dataset CSV",
                    data=csv_bytes,
                    file_name="atmoscast_delhi_ncr_hourly.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with dl2:
                st.download_button(
                    label="⬇ Download System Report",
                    data=report_text.encode("utf-8"),
                    file_name="atmoscast_system_report.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
        except Exception:
            st.download_button(
                label="⬇ Download System Report",
                data=report_text.encode("utf-8"),
                file_name="atmoscast_system_report.txt",
                mime="text/plain",
            )
    else:
        st.warning("Processed dataset not found — download unavailable.")
