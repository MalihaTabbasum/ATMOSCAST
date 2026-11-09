"""
AtmosCast Streamlit Theme & Design System.

Implements the official AtmosCast environmental intelligence visual identity:
- Primary Navy: #102A43
- Teal: #0D9488
- Light Background: #F5F8FA
- Card Background: #FFFFFF
- Status Badges: Soft Green (#22C55E), Amber (#EAB308), Coral (#EF4444)
"""

CUSTOM_CSS = """
<style>
    /* Global Typography & Colors */
    :root {
        --primary-navy: #102A43;
        --secondary-teal: #0D9488;
        --accent-teal: #14B8A6;
        --bg-light: #F5F8FA;
        --card-white: #FFFFFF;
        --text-dark: #1E293B;
        --text-muted: #64748B;
        --border-subtle: #E2E8F0;
        --status-green: #22C55E;
        --status-amber: #EAB308;
        --status-coral: #EF4444;
    }

    .main {
        background-color: var(--bg-light);
        color: var(--text-dark);
        font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
    }

    /* Hero Header Banner */
    .hero-header {
        background: linear-gradient(135deg, #102A43 0%, #1E3A8A 50%, #0D9488 100%);
        border-radius: 14px;
        padding: 1.75rem 2rem;
        color: #FFFFFF;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(16, 42, 67, 0.15);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
        color: #FFFFFF;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #CBD5E1;
        margin: 0.4rem 0 0;
        line-height: 1.45;
    }

    /* Environmental Intelligence Card */
    .atmos-card {
        background: #FFFFFF;
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        margin-bottom: 1rem;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .atmos-card:hover {
        box-shadow: 0 8px 16px -2px rgba(16, 42, 67, 0.08);
        border-color: #CBD5E1;
    }

    /* Metric Value Container */
    .metric-value-box {
        display: flex;
        align-items: baseline;
        gap: 0.4rem;
        margin: 0.3rem 0;
    }
    .metric-number {
        font-size: 1.85rem;
        font-weight: 800;
        color: var(--primary-navy);
        line-height: 1.1;
    }
    .metric-unit {
        font-size: 0.85rem;
        color: var(--text-muted);
        font-weight: 600;
    }

    /* Status Pills */
    .status-pill {
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .status-pill.good {
        background-color: #ECFDF5;
        color: #059669;
        border: 1px solid #A7F3D0;
    }
    .status-pill.satisfactory {
        background-color: #F7FEE7;
        color: #65A30D;
        border: 1px solid #D9F99D;
    }
    .status-pill.moderate {
        background-color: #FEFCE8;
        color: #CA8A04;
        border: 1px solid #FEF08A;
    }
    .status-pill.poor {
        background-color: #FFF7ED;
        color: #EA580C;
        border: 1px solid #FFEDD5;
    }
    .status-pill.very-poor {
        background-color: #FEF2F2;
        color: #DC2626;
        border: 1px solid #FECACA;
    }
    .status-pill.severe {
        background-color: #450A0A;
        color: #FCA5A5;
        border: 1px solid #7F1D1D;
    }

    /* Custom Streamlit adjustments */
    div[data-testid="stMetricValue"] {
        color: var(--primary-navy);
        font-weight: 800;
    }
    .stButton>button {
        background-color: #0D9488;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.25rem;
        border: none;
        transition: background-color 0.15s ease;
    }
    .stButton>button:hover {
        background-color: #0F766E;
    }
</style>
"""
