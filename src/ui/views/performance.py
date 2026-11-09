"""
Model Performance & Validation Benchmarking View for AtmosCast.
"""

from pathlib import Path
import json
import pandas as pd
import streamlit as st

from src.evaluation.plots import plot_model_comparison_bars, plot_horizon_error_trajectory

# Resolve project root relative to this file - works on Streamlit Cloud and locally
_VIEW_DIR = Path(__file__).resolve().parent          # src/ui/views/
_PROJECT_ROOT = _VIEW_DIR.parent.parent.parent       # project root


def _find_path(relative: str) -> Path:
    """Return first existing candidate: project-root/relative or cwd/relative."""
    p1 = _PROJECT_ROOT / relative
    p2 = Path(relative)
    return p1 if p1.exists() else p2


def render_performance_view():
    """
    Renders the Model Performance dashboard comparing Persistence, Random Forest, and XGBoost.
    """
    st.markdown(
        """
        <div class="hero-header">
            <div class="hero-title">Model Evaluation & Validation Benchmarks</div>
            <div class="hero-subtitle">
                Chronological validation model selection and held-out test benchmarks across 24h, 48h, and 72h horizons
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load model registry
    reg_path = _find_path("models/model_registry.json")
    if not reg_path.exists():
        st.warning("Model registry not found. Run Phase 5/6 training pipelines.")
        return

    with open(reg_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    models_data = registry.get("models", [])
    eval_df = pd.DataFrame([
        {
            "horizon": m["horizon"],
            "tier_name": m["tier_name"],
            "model_type": m["model_type"],
            "val_mae": m["val_metrics"]["MAE"],
            "val_rmse": m["val_metrics"]["RMSE"],
            "val_r2": m["val_metrics"]["R2"],
            "test_mae": m["test_metrics"]["MAE"],
            "test_rmse": m["test_metrics"]["RMSE"],
            "test_r2": m["test_metrics"]["R2"],
            "test_mape": m["test_metrics"]["MAPE"],
        }
        for m in models_data
    ])

    # Best Validation Models Summary Cards
    st.markdown("### Top Validation Models by Lookahead Horizon")
    p1, p2, p3 = st.columns(3)

    best_24 = eval_df[eval_df["horizon"] == 24].sort_values(by="val_rmse").iloc[0]
    best_48 = eval_df[eval_df["horizon"] == 48].sort_values(by="val_rmse").iloc[0]
    best_72 = eval_df[eval_df["horizon"] == 72].sort_values(by="val_rmse").iloc[0]

    for col, best_row in zip([p1, p2, p3], [best_24, best_48, best_72]):
        h = best_row["horizon"]
        m_name = best_row["model_type"].replace("_", " ").title()
        t_name = best_row["tier_name"].replace("_", " ").title()
        v_rmse = best_row["val_rmse"]
        v_mae = best_row["val_mae"]
        with col:
            st.markdown(
                f"""
                <div class="atmos-card">
                    <span class="status-pill good">Validation Best</span>
                    <h4 style="margin: 0.5rem 0 0.2rem; color: #102A43;">{h}-Hour Lookahead</h4>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #0D9488;">{m_name}</div>
                    <div style="font-size: 0.8rem; color: #64748B;">{t_name}</div>
                    <div class="metric-value-box" style="margin-top: 0.5rem;">
                        <span class="metric-number" style="font-size: 1.4rem;">{v_rmse:.2f}</span>
                        <span class="metric-unit">Val RMSE (µg/m³)</span>
                    </div>
                    <div style="font-size: 0.78rem; color: #64748B;">Validation MAE: {v_mae:.2f} µg/m³</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Interactive Model Comparison Charts
    st.markdown("### Multi-Model Error Benchmark Across Horizons")
    fig_comp = plot_model_comparison_bars(eval_df)
    st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("---")

    # Horizon Trajectory Line
    st.markdown("### Forecast Error Trajectory (Validation vs. Test)")
    best_df = pd.DataFrame([best_24, best_48, best_72])
    fig_traj = plot_horizon_error_trajectory(best_df)
    st.plotly_chart(fig_traj, use_container_width=True)

    # Scientific Evaluation Transparency Box
    st.markdown("### Evaluation Insights & Acceptance Diagnostics")
    st.markdown(
        r"""
        - **Why Validation XGBoost Outperformed Baseline:** Across all three horizons on the validation set, XGBoost achieved lower RMSE (15.51 - 16.42 µg/m³) than Persistence (17.32 - 21.07 µg/m³).
        - **Weather Feature Contribution:** At the 48-hour horizon, adding surface meteorological features (**Tier 2**) reduced validation error from 16.68 µg/m³ (Tier 1) down to **15.65 µg/m³**.
        - **Why Test Errors Are Higher (Peak Compression):** The held-out test split captures the unprecedented peak of the January 6–7 severe episode (> 220 µg/m³). Decision-tree ensembles cannot extrapolate beyond the maximum threshold observed in training data, causing expected peak compression.
        """
    )
