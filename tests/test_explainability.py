"""
Unit Tests for AtmosCast Explainable AI & Atmospheric Insights (Phase 7).

Verifies:
- SHAP TreeExplainer initialization and schema matching with trained models
- Computation of SHAP values and base value E[f(X)]
- Global feature importance ranking and functional group categorization
- Group attribution summing to 100%
- Local waterfall decomposition consistency (base_value + sum(shap) == prediction)
- Generation and validity of all 4 interactive Plotly figures
- Verification of explainable AI report content and scientific integrity sections
"""

from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from src.evaluation.evaluator import ModelEvaluator
from src.explainability.explainer import ModelExplainer
from src.explainability.plots import (
    plot_global_shap_importance,
    plot_feature_group_importance,
    plot_waterfall_explanation,
    plot_shap_dependence,
)


@pytest.fixture
def explainer_and_data():
    artifact_path = Path("models/xgboost_tier2_pollution_and_weather_pm25_h48.joblib")
    assert artifact_path.exists(), f"Model artifact missing at {artifact_path}"
    explainer = ModelExplainer(artifact_path)

    evaluator = ModelEvaluator(target_pollutant="pm25", horizons=[48])
    df, feature_tiers = evaluator.load_and_engineer()
    features = feature_tiers["tier2_pollution_and_weather"]
    split_data = evaluator.get_split_data(df, features, 48)

    return explainer, split_data["X_test"]


class TestModelExplainer:
    def test_compute_shap_values_shapes(self, explainer_and_data):
        explainer, X_test = explainer_and_data
        shap_values, base_val = explainer.compute_shap_values(X_test.iloc[:10])

        assert shap_values.shape == (10, len(explainer.feature_names))
        assert isinstance(base_val, float)
        assert base_val > 50.0  # PM2.5 base value should be positive and realistic

    def test_get_global_importance(self, explainer_and_data):
        explainer, X_test = explainer_and_data
        importance_df = explainer.get_global_importance(X_test.iloc[:20], top_n=10)

        assert len(importance_df) == 10
        assert list(importance_df.columns) == ["feature", "mean_abs_shap", "group"]
        # Verify descending order
        assert (importance_df["mean_abs_shap"].diff().dropna() <= 0).all()

    def test_get_group_contributions_percentage_sum(self, explainer_and_data):
        explainer, X_test = explainer_and_data
        group_df = explainer.get_group_contributions(X_test.iloc[:20])

        assert len(group_df) > 0
        assert "group" in group_df.columns
        assert "percentage" in group_df.columns
        # Percentage sum should be approximately 100%
        assert np.isclose(group_df["percentage"].sum(), 100.0, atol=1.0)
        assert "Pollution History" in group_df["group"].values
        assert "Surface Meteorology" in group_df["group"].values

    def test_explain_single_prediction_conservation(self, explainer_and_data):
        explainer, X_test = explainer_and_data
        row = X_test.iloc[0]
        explanation = explainer.explain_single_prediction(row, top_n=5)

        assert "base_value" in explanation
        assert "prediction" in explanation
        assert "top_contributions" in explanation
        assert len(explanation["top_contributions"]) == 5

        # Check additivity: base_value + sum(shap_values) == prediction
        full_df = explanation["full_shap_df"]
        reconstructed = explanation["base_value"] + full_df["shap_value"].sum()
        assert np.isclose(reconstructed, explanation["prediction"], atol=0.5)


class TestExplainabilityPlots:
    def test_plot_global_shap_importance(self):
        df = pd.DataFrame({
            "feature": ["wind_speed_10m", "pm25_lag_1", "temperature_2m"],
            "mean_abs_shap": [4.5, 3.2, 1.8],
            "group": ["Surface Meteorology", "Pollution History", "Surface Meteorology"],
        })
        fig = plot_global_shap_importance(df, horizon=48, model_name="XGBoost")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1

    def test_plot_feature_group_importance(self):
        df = pd.DataFrame({
            "group": ["Pollution History", "Surface Meteorology", "Temporal & Diurnal Cycles"],
            "percentage": [52.0, 46.0, 2.0],
        })
        fig = plot_feature_group_importance(df, horizon=48)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1

    def test_plot_waterfall_explanation(self):
        explanation = {
            "base_value": 110.0,
            "prediction": 135.0,
            "top_contributions": [
                {"feature": "pm25_roll_mean_24h", "value": 150.0, "shap_value": 15.0},
                {"feature": "wind_speed_10m", "value": 2.5, "shap_value": 10.0},
            ],
        }
        fig = plot_waterfall_explanation(explanation)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1

    def test_plot_shap_dependence(self):
        feature_vals = np.array([2.0, 5.0, 8.0, 12.0])
        shap_vals = np.array([6.0, 1.0, -2.0, -5.0])
        fig = plot_shap_dependence(feature_vals, shap_vals, feature_name="wind_speed_10m")
        assert isinstance(fig, go.Figure)


class TestExplainabilityArtifacts:
    def test_figures_exist_and_non_empty(self):
        figures_dir = Path("reports/figures")
        expected_files = [
            "shap_global_importance.html",
            "shap_feature_groups.html",
            "shap_episode_waterfall.html",
            "shap_weather_dependence.html",
        ]
        for fname in expected_files:
            fpath = figures_dir / fname
            assert fpath.exists(), f"Figure missing: {fpath}"
            assert fpath.stat().st_size > 1000

    def test_explainable_ai_report_exists_and_populated(self):
        report_path = Path("reports/explainable_ai_report.md")
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "Executive Summary for Non-Technical Stakeholders" in content
        assert "Macro Feature Group Attribution" in content
        assert "Planetary Boundary Layer (PBL) Height Investigation" in content
        assert "Atmospheric Inversion Strength Investigation" in content
        assert "Regional Fire Activity & Stubble-Burning Investigation" in content
        assert "Crucial Scientific Guardrail" in content
