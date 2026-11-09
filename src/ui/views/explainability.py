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
    st.markdown(
        """
        <div class="hero-header">
            <div class="hero-title">Explainable AI & Atmospheric Attribution</div>
            <div class="hero-subtitle">
                Cooperative game-theoretic SHAP (TreeExplainer) insights into 48-hour PM2.5 forecasting dynamics
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Non-Technical Summary Banner
    st.markdown(
        r"""
        ### What Drives the 48-Hour Forecast? (Plain-Language Summary)
        - 🌫️ **Pollution Baseline (52.1% Share):** The city's current air quality and 24-hour rolling averages act as a baseline foundation. High antecedent particulate matter takes time to clear.
        - 💨 **Surface Wind Speed (Primary Steering Factor):** When wind speed drops below **5 km/h**, horizontal ventilation collapses, trapping emissions near the ground and pushing forecasts upward.
        - 💧 **Moisture Catalyst:** High relative humidity (> 85%) sharply elevates predicted concentrations, capturing secondary inorganic aerosol formation (gas-to-particle conversion).
        - ☀️ **Diurnal Mixing:** Daytime solar heating expands the boundary layer, while nocturnal radiative cooling locks in emissions.
        """
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
    st.markdown("### Global Feature Attribution Breakdown")
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
    st.markdown("### Dissecting an Individual Prediction: Severe Smog Surge (January 5–6, 2024)")
    peak_idx = y_test.idxmax()
    peak_row = X_test.loc[peak_idx]
    peak_actual = float(y_test.loc[peak_idx])
    peak_explanation = explainer.explain_single_prediction(peak_row, top_n=6)

    fig_waterfall = plot_waterfall_explanation(
        peak_explanation,
        sample_title=f"Severe Smog Peak (Actual PM2.5: {peak_actual:.1f} µg/m³)"
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

    st.markdown("---")

    # Meteorological Non-Linear Dependence
    st.markdown("### Non-Linear Stagnation Threshold: Wind Speed vs. SHAP Impact")
    shap_matrix, _ = explainer.compute_shap_values(X_test)
    wind_idx = explainer.feature_names.index("wind_speed_10m")
    wind_vals = X_test["wind_speed_10m"].to_numpy()
    wind_shap = shap_matrix[:, wind_idx]

    fig_dep = plot_shap_dependence(wind_vals, wind_shap, feature_name="wind_speed_10m", display_title="10m Wind Speed", unit="km/h")
    st.plotly_chart(fig_dep, use_container_width=True)

    # Scientific Integrity Guardrails Box
    st.markdown("### Scientific Attribution Guardrails")
    st.info(
        "⚖️ **Causality vs. Association:** SHAP values measure statistical feature attribution inside the machine learning model. They do NOT prove physical causality. High attribution reflects strong predictive association, not that a variable emits pollutants."
    )
