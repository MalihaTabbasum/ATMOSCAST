"""
Explainable AI (SHAP) View for AtmosCast.
"""

from pathlib import Path
import pandas as pd
import streamlit as st

from src.explainability.explainer import ModelExplainer
from src.explainability.plots import (
    plot_global_shap_importance,
    plot_feature_group_importance,
    plot_waterfall_explanation,
    plot_shap_dependence,
)
from src.ui.theme import render_page_header

# Resolve project root relative to this file - works on Streamlit Cloud and locally
_VIEW_DIR = Path(__file__).resolve().parent          # src/ui/views/
_PROJECT_ROOT = _VIEW_DIR.parent.parent.parent       # project root


def _find_artifact(relative: str) -> Path:
    """Return first existing candidate: project-root/relative or cwd/relative."""
    p1 = _PROJECT_ROOT / relative
    p2 = Path(relative)
    return p1 if p1.exists() else p2


@st.cache_resource
def get_cached_explainer():
    """Loads and caches the ModelExplainer for the 48h XGBoost Tier 2 model."""
    artifact_path = _find_artifact(
        "models/xgboost_tier2_pollution_and_weather_pm25_h48.joblib"
    )
    if not artifact_path.exists():
        return None
    return ModelExplainer(artifact_path)


def render_explainability_view(sample_df: pd.DataFrame):
    """
    Renders the Explainable AI (SHAP) dashboard.
    """
    render_page_header(
        kicker="COOPERATIVE GAME-THEORETIC ATTRIBUTION",
        title="Explainable AI & Atmospheric Feature Attribution (TreeSHAP)",
        subtitle="Decomposing the 48-hour XGBoost forecasting model into exact marginal attributions across antecedent pollution history, surface meteorology, and calendar cycles.",
    )

    # Executive Summary Card
    st.markdown(
        """
        <div class="intel-brief">
            <div class="intel-brief-title">Executive Attribution Summary: What Drives 48-Hour Projections?</div>
            <p class="intel-brief-body">
                <strong>Pollution Momentum (52.1% Macro Share):</strong> Current particulate concentration and 24h rolling averages establish the baseline trajectory; high antecedent burden requires sustained ventilation to clear.<br>
                <strong>Surface Wind Speed (Primary Atmospheric Gate):</strong> Below 5.4 km/h (1.5 m/s), ventilation collapses, driving model attributions sharply upward due to emissions stagnation.<br>
                <strong>Relative Humidity (Secondary Aerosol Driver):</strong> High humidity (> 85%) significantly increases predicted concentrations, capturing aqueous gas-to-particle conversion.<br>
                <strong>Diurnal Thermodynamics:</strong> Captures boundary-layer expansion during daylight and compression under nocturnal radiation cooling.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    explainer = get_cached_explainer()
    if explainer is None:
        st.warning("Model artifact not found. Please verify Phase 5 model training.")
        return

    # Ingest test slice for SHAP
    from src.evaluation.evaluator import ModelEvaluator
    evaluator = ModelEvaluator(target_pollutant="pm25", horizons=[48])
    df, feature_tiers = evaluator.load_and_engineer()
    features = feature_tiers["tier2_pollution_and_weather"]
    split_data = evaluator.get_split_data(df, features, 48)
    X_test = split_data["X_test"]
    y_test = split_data["y_test"]

    # Global SHAP & Group Share Columns
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.5rem;'>Global Atmospheric Feature Importance Hierarchy</div>",
        unsafe_allow_html=True,
    )
    c_left, c_right = st.columns([3, 2])

    with c_left:
        global_imp = explainer.get_global_importance(X_test, top_n=12)
        fig_global = plot_global_shap_importance(global_imp, horizon=48, model_name="XGBoost Tier 2")
        st.plotly_chart(fig_global, use_container_width=True)

    with c_right:
        group_df = explainer.get_group_contributions(X_test)
        fig_group = plot_feature_group_importance(group_df, horizon=48)
        st.plotly_chart(fig_group, use_container_width=True)

    st.markdown("---")

    # Local Waterfall Prediction Decomposition
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.5rem;'>Single-Observation Waterfall Decomposition: Severe Smog Episode</div>",
        unsafe_allow_html=True,
    )
    peak_idx = y_test.idxmax()
    peak_row = X_test.loc[peak_idx]
    peak_actual = float(y_test.loc[peak_idx])
    peak_explanation = explainer.explain_single_prediction(peak_row, top_n=6)

    fig_waterfall = plot_waterfall_explanation(
        peak_explanation,
        sample_title=f"Severe Smog Peak (Observed PM2.5: {peak_actual:.1f} µg/m³)"
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

    st.markdown("---")

    # Meteorological Non-Linear Dependence
    st.markdown(
        "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 1.05rem; font-weight: 700; color: #172B4D; margin-bottom: 0.5rem;'>Non-Linear Stagnation Threshold: 10m Wind Speed vs. Model Attribution</div>",
        unsafe_allow_html=True,
    )
    shap_matrix, _ = explainer.compute_shap_values(X_test)
    wind_idx = explainer.feature_names.index("wind_speed_10m")
    wind_vals = X_test["wind_speed_10m"].to_numpy()
    wind_shap = shap_matrix[:, wind_idx]

    fig_dep = plot_shap_dependence(wind_vals, wind_shap, feature_name="wind_speed_10m", display_title="10m Wind Speed", unit="km/h")
    st.plotly_chart(fig_dep, use_container_width=True)

    # Scientific Integrity Guardrails Box
    st.markdown(
        """
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.85rem 1.15rem; margin-top: 1rem; font-size: 0.78rem; color: #64748B; line-height: 1.45;">
            <strong style="color: #172B4D;">Statistical Association vs. Physical Causality:</strong>
            TreeSHAP values quantify cooperative game-theoretic feature attribution inside the machine learning model. High SHAP attribution reflects strong statistical predictive association—it does NOT imply that a meteorological variable is an emission source.
        </div>
        """,
        unsafe_allow_html=True,
    )
