"""
Model Performance & Validation Benchmarking View for AtmosCast.
"""

from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.evaluation.plots import plot_model_comparison_bars, plot_horizon_error_trajectory
from src.ui.theme import render_page_header, apply_custom_chart_theme

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
    Renders the Model Performance dashboard comparing Persistence, Random Forest, and XGBoost,
    including an interactive Model Comparison Laboratory and held-out test diagnostics.
    """
    render_page_header(
        kicker="DIAGNOSTIC BENCHMARKING & MODEL SELECTION",
        title="Model Evaluation & Multi-Horizon Benchmarks",
        subtitle="Chronological train/val/test evaluation comparing Persistence baseline, Random Forest, and XGBoost across 24h, 48h, and 72h lead times.",
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

    best_24 = eval_df[eval_df["horizon"] == 24].sort_values(by="val_rmse").iloc[0]
    best_48 = eval_df[eval_df["horizon"] == 48].sort_values(by="val_rmse").iloc[0]
    best_72 = eval_df[eval_df["horizon"] == 72].sort_values(by="val_rmse").iloc[0]

    # Main Navigation Tabs: Validation Summary, Model Comparison Lab, Diagnostics
    p_tab1, p_tab2, p_tab3 = st.tabs([
        "Top Validation Models & Benchmarks",
        "Interactive Model Comparison Laboratory",
        "Held-Out Test Set & Scientific Insights",
    ])

    with p_tab1:
        st.markdown(
            "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin: 0.5rem 0 0.5rem;'>Optimal Model Architectures by Forecast Horizon</div>",
            unsafe_allow_html=True,
        )
        p1, p2, p3 = st.columns(3)

        for col, best_row in zip([p1, p2, p3], [best_24, best_48, best_72]):
            h = best_row["horizon"]
            m_name = best_row["model_type"].replace("_", " ").title()
            t_name = best_row["tier_name"].replace("_", " ").title()
            v_rmse = best_row["val_rmse"]
            v_mae = best_row["val_mae"]
            t_rmse = best_row["test_rmse"]
            with col:
                st.markdown(
                    f"""
                    <div class="atmos-card">
                        <div class="card-top-row">
                            <span class="card-label">Horizon {h} Hours</span>
                            <span class="status-pill good"><span class="pill-dot"></span>Validation Best</span>
                        </div>
                        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.15rem; font-weight: 700; color: #0D9488; margin: 0.2rem 0;">{m_name}</div>
                        <div style="font-size: 0.78rem; color: #64748B;">{t_name}</div>
                        <div class="metric-value-box">
                            <span class="metric-number">{v_rmse:.2f}</span>
                            <span class="metric-unit">Val RMSE (µg/m³)</span>
                        </div>
                        <div class="card-footer-meta">
                            Val MAE: {v_mae:.2f} µg/m³ • Held-Out Test RMSE: {t_rmse:.2f} µg/m³
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # Visualizations
        st.markdown(
            "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.5rem;'>Multi-Horizon Validation & Test Error Distributions</div>",
            unsafe_allow_html=True,
        )
        fig_comp = plot_model_comparison_bars(eval_df)
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("---")

        st.markdown(
            "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.5rem;'>Horizon Error Growth Trajectory (Validation vs. Held-Out Test)</div>",
            unsafe_allow_html=True,
        )
        best_df = pd.DataFrame([best_24, best_48, best_72])
        fig_traj = plot_horizon_error_trajectory(best_df)
        st.plotly_chart(fig_traj, use_container_width=True)

    with p_tab2:
        # Interactive Model Comparison Laboratory
        st.markdown(
            "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.4rem;'>Interactive Model Benchmarking Laboratory</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size: 0.82rem; color: #64748B; margin-bottom: 0.75rem;'>Select target evaluation metric and forecast horizon to dynamically rank all 9 trained model configurations.</div>",
            unsafe_allow_html=True,
        )

        lab_c1, lab_c2 = st.columns(2)
        with lab_c1:
            metric_selected = st.selectbox(
                "Evaluation Metric",
                options=["val_rmse", "val_mae", "test_rmse", "test_mae", "test_r2", "test_mape"],
                format_func=lambda x: {
                    "val_rmse": "Validation RMSE (µg/m³) — Lower is Better",
                    "val_mae": "Validation MAE (µg/m³) — Lower is Better",
                    "test_rmse": "Held-Out Test RMSE (µg/m³) — Lower is Better",
                    "test_mae": "Held-Out Test MAE (µg/m³) — Lower is Better",
                    "test_r2": "Held-Out Test R² Score — Higher is Better",
                    "test_mape": "Held-Out Test MAPE (%) — Lower is Better",
                }[x],
            )
        with lab_c2:
            horizon_filter = st.selectbox(
                "Forecast Horizon",
                options=[0, 24, 48, 72],
                format_func=lambda x: "All Horizons (24h, 48h, 72h)" if x == 0 else f"{x}-Hour Horizon Only",
            )

        lab_df = eval_df.copy()
        if horizon_filter > 0:
            lab_df = lab_df[lab_df["horizon"] == horizon_filter]

        ascending = not ("r2" in metric_selected)
        lab_df = lab_df.sort_values(by=metric_selected, ascending=ascending)

        lab_df["display_label"] = (
            lab_df["model_type"].str.replace("_", " ").str.title() + " " +
            lab_df["tier_name"].str.replace("_", " ").str.title() + " (h=" +
            lab_df["horizon"].astype(str) + "h)"
        )

        fig_lab = go.Figure()
        fig_lab.add_trace(go.Bar(
            x=lab_df["display_label"],
            y=lab_df[metric_selected],
            marker_color="#0D9488",
            hovertemplate="Model: %{x}<br>Value: <b>%{y:.2f}</b><extra></extra>",
        ))
        fig_lab.update_xaxes(tickangle=40)
        fig_lab.update_yaxes(title=metric_selected.upper())
        fig_lab = apply_custom_chart_theme(fig_lab, height=450, title=f"Model Configurations Ranked by {metric_selected.upper()}")
        st.plotly_chart(fig_lab, use_container_width=True)

        st.markdown("### Granular Model Evaluation Metrics Table")
        display_lab_cols = ["model_type", "tier_name", "horizon", "val_rmse", "val_mae", "test_rmse", "test_mae", "test_r2", "test_mape"]
        st.dataframe(lab_df[display_lab_cols], use_container_width=True)

    with p_tab3:
        st.markdown(
            """
            <div class="intel-brief">
                <div class="intel-brief-title">Diagnostic Methodology & Test Distribution Shift Analysis</div>
                <p class="intel-brief-body">
                    <strong>1. Model Selection on Chronological Validation:</strong><br>
                    Across all three horizons on the chronological validation set, XGBoost achieved superior RMSE (15.51–16.42 µg/m³) compared to Persistence baseline (17.32–21.07 µg/m³). Decision-tree ensembles captured the diurnal boundary-layer rhythm and ventilation cycles effectively.<br><br>
                    <strong>2. Marginal Value of Meteorological Coupling:</strong><br>
                    At the 48-hour horizon, integrating surface meteorological predictors (Tier 2) reduced validation error from 16.68 µg/m³ (Tier 1 pollution-only) down to <strong>15.65 µg/m³</strong>, validating the core SIH26082 hypothesis that atmospheric coupling enhances predictive skill.<br><br>
                    <strong>3. Held-Out Test Set Peak Compression & Negative R²:</strong><br>
                    The held-out test split (Jan 6–7) captures the acute peak of the severe winter episode (> 220 µg/m³ PM2.5). Tree-based ensembles cannot predict values outside the range observed in the training distribution, leading to peak compression. On this acute episode, the simple Persistence baseline (which carries forward the already surging antecedent observation) achieved lower test RMSE at h=24h, while direct XGBoost models minimized compounding error across multi-day rollouts.<br><br>
                    <strong>4. Direct Multi-Horizon vs. Recursive Rollout:</strong><br>
                    AtmosCast trains independent estimators for each horizon hour h ∈ {24, 48, 72}h rather than iteratively feeding predicted values back into the feature set. This guarantees zero autoregressive error magnification over the 72-hour window.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
