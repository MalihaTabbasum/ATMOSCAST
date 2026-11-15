"""
AtmosCast Design System & SaaS Environmental Intelligence Theme.

Design Direction:
- Primary background: #F6F8FA
- Sidebar background: #102A43
- Primary accent: #0D9488 (Teal)
- Secondary accent: #38BDF8 (Sky Blue)
- Text primary: #172B4D (Deep Charcoal Navy)
- Text secondary: #64748B (Slate Muted)
- Card background: #FFFFFF
- Critical indicator: #EF6461 (Coral Red)
- Warning indicator: #F59E0B (Amber)
- Typography: Inter & JetBrains Mono (data/telemetry)
"""

import plotly.graph_objects as go
import streamlit as st

CUSTOM_CSS = """
<style>
    /* ── Web Fonts: Inter, Plus Jakarta Sans, JetBrains Mono ──────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

    /* ── Design System Variables ──────────────────────────────────────────── */
    :root {
        --bg-app: #F6F8FA;
        --sidebar-bg: #102A43;
        --accent-primary: #0D9488;
        --accent-secondary: #38BDF8;
        --text-primary: #172B4D;
        --text-secondary: #64748B;
        --text-light: #94A3B8;
        --surface-card: #FFFFFF;
        --indicator-critical: #EF6461;
        --indicator-warning: #F59E0B;
        --indicator-success: #10B981;
        --border-subtle: #E2E8F0;
        --border-strong: #CBD5E1;
        --shadow-subtle: 0 1px 3px 0 rgba(15, 23, 42, 0.05), 0 1px 2px -1px rgba(15, 23, 42, 0.03);
        --shadow-hover: 0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.04);
        --radius-sm: 6px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-full: 9999px;
    }

    /* ── Base App Container ───────────────────────────────────────────────── */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg-app) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    /* ── Compact & Elegant Dark Navy Sidebar ─────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding-top: 1rem;
    }

    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }

    /* Sidebar Radio Navigation Link Items */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 0.2rem;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        background: transparent;
        padding: 0.5rem 0.75rem;
        border-radius: var(--radius-sm);
        margin: 0;
        font-size: 0.83rem !important;
        font-weight: 500 !important;
        color: #CBD5E1 !important;
        transition: all 0.15s ease-in-out;
        border-left: 3px solid transparent;
        cursor: pointer;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: rgba(255, 255, 255, 0.08);
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"],
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
        background: rgba(13, 148, 136, 0.22) !important;
        color: #38BDF8 !important;
        font-weight: 600 !important;
        border-left: 3px solid #0D9488 !important;
    }

    /* Sidebar Selectbox */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-radius: var(--radius-sm);
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] * {
        color: #FFFFFF !important;
    }

    /* ── Persistent Command Topbar ────────────────────────────────────────── */
    .system-topbar {
        background: var(--surface-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 0.65rem 1.15rem;
        margin-bottom: 1.25rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.75rem;
        box-shadow: var(--shadow-subtle);
    }
    .topbar-left {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
    }
    .topbar-brand {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800;
        font-size: 0.95rem;
        letter-spacing: 0.06em;
        color: var(--text-primary);
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .topbar-divider {
        width: 1px;
        height: 16px;
        background-color: var(--border-subtle);
    }
    .topbar-meta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: var(--text-secondary);
    }
    .live-beacon {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        color: #047857;
        background: #ECFDF5;
        border: 1px solid #A7F3D0;
        padding: 0.18rem 0.55rem;
        border-radius: var(--radius-full);
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .beacon-dot {
        width: 6px;
        height: 6px;
        background-color: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: beacon-pulse 2s infinite cubic-bezier(0.66, 0, 0, 1);
    }
    @keyframes beacon-pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* ── Professional Page Headers ────────────────────────────────────────── */
    .page-header-container {
        margin-bottom: 1.25rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border-subtle);
    }
    .page-kicker {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--accent-primary);
        margin-bottom: 0.25rem;
    }
    .page-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        color: var(--text-primary);
        margin: 0;
        line-height: 1.2;
    }
    .page-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
        color: var(--text-secondary);
        margin-top: 0.35rem;
        line-height: 1.45;
        max-width: 950px;
    }

    /* ── Instrument-Grade Metric Card (.atmos-card) ───────────────────────── */
    .atmos-card {
        background: var(--surface-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 1rem 1.15rem;
        box-shadow: var(--shadow-subtle);
        margin-bottom: 0.75rem;
        transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
    }
    .atmos-card:hover {
        border-color: var(--border-strong);
        box-shadow: var(--shadow-hover);
        transform: translateY(-1px);
    }

    .card-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.35rem;
    }
    .card-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-secondary);
    }

    .metric-value-box {
        display: flex;
        align-items: baseline;
        gap: 0.4rem;
        margin: 0.2rem 0 0.3rem 0;
    }
    .metric-number {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1;
        letter-spacing: -0.03em;
        font-variant-numeric: tabular-nums;
    }
    .metric-unit {
        font-family: 'Inter', sans-serif;
        font-size: 0.78rem;
        color: var(--text-secondary);
        font-weight: 600;
    }
    .card-footer-meta {
        font-family: 'Inter', sans-serif;
        font-size: 0.74rem;
        color: var(--text-secondary);
        line-height: 1.35;
        border-top: 1px solid #F1F5F9;
        padding-top: 0.4rem;
        margin-top: 0.4rem;
    }

    /* ── Status Pills & CPCB AQI Badges ───────────────────────────────────── */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.18rem 0.55rem;
        border-radius: var(--radius-full);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        line-height: 1.2;
    }
    .pill-dot {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background-color: currentColor;
    }

    .status-pill.good {
        background-color: #ECFDF5;
        color: #047857;
        border: 1px solid #A7F3D0;
    }
    .status-pill.satisfactory {
        background-color: #F7FEE7;
        color: #4D7C0F;
        border: 1px solid #D9F99D;
    }
    .status-pill.moderate {
        background-color: #FFFBEB;
        color: #B45309;
        border: 1px solid #FDE68A;
    }
    .status-pill.poor {
        background-color: #FFF7ED;
        color: #C2410C;
        border: 1px solid #FFEDD5;
    }
    .status-pill.very-poor {
        background-color: #FEF2F2;
        color: #B91C1C;
        border: 1px solid #FECACA;
    }
    .status-pill.severe {
        background-color: #450A0A;
        color: #FCA5A5;
        border: 1px solid #7F1D1D;
    }

    /* ── Health Alert & Advisory Banner ───────────────────────────────────── */
    .alert-banner {
        background: #FFFFFF;
        border: 1px solid #FECACA;
        border-left: 4px solid var(--indicator-critical);
        border-radius: var(--radius-md);
        padding: 0.85rem 1.15rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-subtle);
    }
    .alert-banner-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.88rem;
        font-weight: 700;
        color: #991B1B;
        display: flex;
        align-items: center;
        gap: 0.45rem;
        margin-bottom: 0.25rem;
    }
    .alert-banner-body {
        font-size: 0.82rem;
        color: #334155;
        line-height: 1.45;
        margin: 0;
    }

    /* ── Intelligence Briefing Callout (.intel-brief) ─────────────────────── */
    .intel-brief {
        background: #FFFFFF;
        border: 1px solid var(--border-subtle);
        border-left: 4px solid var(--accent-primary);
        border-radius: var(--radius-md);
        padding: 0.85rem 1.15rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-subtle);
    }
    .intel-brief-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.88rem;
        font-weight: 700;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 0.4rem;
        margin-bottom: 0.25rem;
    }
    .intel-brief-body {
        font-size: 0.82rem;
        color: #334155;
        line-height: 1.45;
        margin: 0;
    }

    /* ── Streamlit Element Overrides ──────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: var(--surface-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 0.85rem 1rem;
        box-shadow: var(--shadow-subtle);
    }
    [data-testid="stMetricLabel"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.68rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: var(--text-secondary) !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        color: var(--text-primary) !important;
        font-size: 1.55rem !important;
        font-weight: 700 !important;
        font-variant-numeric: tabular-nums !important;
    }
    [data-testid="stMetricDelta"] {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.74rem !important;
        font-weight: 600 !important;
    }

    /* Primary Action Buttons */
    .stButton > button {
        background-color: var(--accent-primary) !important;
        color: #FFFFFF !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 0.45rem 1.15rem !important;
        border: 1px solid transparent !important;
        box-shadow: 0 1px 2px rgba(13, 148, 136, 0.15) !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        background-color: #0F766E !important;
        box-shadow: 0 2px 4px rgba(13, 148, 136, 0.25) !important;
    }

    /* Download Buttons */
    .stDownloadButton > button {
        background-color: #FFFFFF !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        padding: 0.4rem 0.95rem !important;
        transition: all 0.15s ease !important;
    }
    .stDownloadButton > button:hover {
        background-color: #F8FAFC !important;
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid var(--border-subtle);
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.84rem;
        color: var(--text-secondary);
        padding: 0.5rem 0.85rem;
        border-radius: var(--radius-sm) var(--radius-sm) 0 0;
    }
    .stTabs [aria-selected="true"] {
        color: var(--accent-primary) !important;
        border-bottom: 2px solid var(--accent-primary) !important;
        background: transparent !important;
    }

    /* Dividers */
    hr {
        margin: 1.5rem 0 !important;
        border: none !important;
        border-top: 1px solid var(--border-subtle) !important;
    }
</style>
"""


def apply_custom_chart_theme(
    fig: go.Figure,
    height: int = 420,
    title: str = "",
    show_legend: bool = True,
) -> go.Figure:
    """
    Applies the cohesive SaaS environmental intelligence theme to a Plotly figure:
    - Background: Crisp White (#FFFFFF)
    - Gridlines: Light Slate (#E2E8F0)
    - Tooltip: Dark Navy (#102A43) with Tabular Numerals
    - Standardized typography and horizontal legend placement
    """
    layout_update = dict(
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
            color="#172B4D",
            size=12,
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=height,
        margin=dict(l=48, r=32, t=50 if title else 28, b=40),
        hoverlabel=dict(
            bgcolor="#102A43",
            font_size=12,
            font_family="JetBrains Mono, monospace",
            font_color="#FFFFFF",
            bordercolor="#334155",
        ),
    )

    if title:
        layout_update["title"] = dict(
            text=f"<b>{title}</b>",
            font=dict(
                family="Plus Jakarta Sans, sans-serif",
                size=14,
                color="#172B4D",
            ),
            x=0.01,
            xanchor="left",
            y=0.96,
        )

    if show_legend:
        layout_update["legend"] = dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            font=dict(size=11, color="#475569"),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#E2E8F0",
            borderwidth=1,
        )

    fig.update_layout(**layout_update)

    # Style axes
    fig.update_xaxes(
        gridcolor="#E2E8F0",
        zerolinecolor="#CBD5E1",
        tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#64748B"),
        title_font=dict(size=11, color="#475569"),
    )
    fig.update_yaxes(
        gridcolor="#E2E8F0",
        zerolinecolor="#CBD5E1",
        tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#64748B"),
        title_font=dict(size=11, color="#475569"),
    )

    return fig


def render_page_header(kicker: str, title: str, subtitle: str) -> None:
    """Renders a clean, editorial-grade page header."""
    st.markdown(
        f"""
        <div class="page-header-container">
            <div class="page-kicker">{kicker}</div>
            <h1 class="page-title">{title}</h1>
            <div class="page-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_command_topbar(station_name: str, station_code: str, coords: str, timestamp_ist: str) -> None:
    """Renders the persistent environmental observatory status bar."""
    st.markdown(
        f"""
        <div class="system-topbar">
            <div class="topbar-left">
                <span class="live-beacon">
                    <span class="beacon-dot"></span>
                    Live Telemetry
                </span>
                <span class="topbar-divider"></span>
                <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #172B4D; font-size: 0.88rem;">
                    {station_name}
                </span>
                <span class="topbar-meta">[{station_code}]</span>
                <span class="topbar-divider"></span>
                <span class="topbar-meta">📍 {coords}</span>
            </div>
            <div class="topbar-meta">
                Observation IST: <strong style="color: #0D9488;">{timestamp_ist}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_health_alert(aqi_val: float, category: str, prominent: str) -> None:
    """Renders statutory CPCB health advisory & Graded Response Action Plan (GRAP) stage."""
    grap_stage = "Stage I (Poor)"
    advisory = "People with respiratory illness should limit prolonged outdoor exertion."

    if aqi_val > 400 or category == "Severe":
        grap_stage = "GRAP Stage IV (Severe+ / Emergency)"
        advisory = "Emergency air quality regime. Healthy individuals experience respiratory illness; vulnerable groups face severe cardiovascular and pulmonary risk. Avoid all outdoor physical activity."
    elif aqi_val > 300 or category == "Very Poor":
        grap_stage = "GRAP Stage III (Severe / Very Poor)"
        advisory = "Prolonged exposure triggers respiratory illness in most people. Children, elderly, and those with heart/lung disease should remain indoors."
    elif aqi_val > 200 or category == "Poor":
        grap_stage = "GRAP Stage II (Very Poor / Poor)"
        advisory = "Breathing discomfort to most people on prolonged exposure. Sensitive groups should wear N95 filtration masks outdoors."
    elif aqi_val > 100 or category == "Moderate":
        grap_stage = "GRAP Stage I (Moderate)"
        advisory = "Breathing discomfort to people with lungs, asthma, and heart diseases."
    else:
        grap_stage = "Normal Air Quality"
        advisory = "Air quality is satisfactory; air pollution poses little or no health risk."

    st.markdown(
        f"""
        <div class="alert-banner">
            <div class="alert-banner-title">
                ⚠️ Statutory Public Health Advisory • {grap_stage}
            </div>
            <p class="alert-banner-body">
                <strong>Current CPCB NAQI: {aqi_val:.0f} ({category.upper()})</strong> • Prominent Pollutant: <strong>{prominent}</strong>.<br>
                {advisory}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
