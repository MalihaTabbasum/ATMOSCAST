"""
Unit Tests for AtmosCast Model Evaluation and Validation (Phase 6).

Verifies:
- Chronological evaluation across validation and test sets
- Validation-driven model selection without test leakage
- Episode-specific performance metrics and Mean Bias Error (MBE) computation
- Atmospheric stability regime performance stratification
- Generation and validity of all 6 interactive Plotly diagnostic figures
- Integrity of the formal validation evaluation report
"""

from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from src.evaluation.evaluator import ModelEvaluator
from src.evaluation.pipeline import EvaluationPipeline
from src.evaluation.plots import (
    plot_actual_vs_predicted,
    plot_residuals_diagnostic,
    plot_model_comparison_bars,
    plot_horizon_error_trajectory,
    plot_regime_performance,
    plot_severe_episode_errors,
)


@pytest.fixture
def evaluator():
    return ModelEvaluator(
        data_path="data/processed/merged_delhi_ncr_hourly.csv",
        models_dir="models",
        target_pollutant="pm25",
        horizons=[24, 48, 72],
    )


class TestModelEvaluator:
    def test_load_and_engineer(self, evaluator):
        df, tiers = evaluator.load_and_engineer()
        assert len(df) == 1008
        assert "tier1_pollution_only" in tiers
        assert "tier2_pollution_and_weather" in tiers
        assert "tier3_coupled_atmospheric" in tiers

    def test_evaluate_all_models_metrics_presence(self, evaluator):
        df, tiers = evaluator.load_and_engineer()
        eval_df = evaluator.evaluate_all_models(df, tiers)

        assert len(eval_df) == 27
        for col in ["val_mae", "val_rmse", "val_r2", "val_mbe", "test_mae", "test_rmse", "test_r2", "test_mbe"]:
            assert col in eval_df.columns
            assert not eval_df[col].isna().any()

    def test_select_best_models_on_validation_isolation(self, evaluator):
        df, tiers = evaluator.load_and_engineer()
        eval_df = evaluator.evaluate_all_models(df, tiers)
        best_models = evaluator.select_best_models_on_validation(eval_df)

        assert len(best_models) == 3
        assert list(best_models["horizon"]) == [24, 48, 72]

        # Verify that selection chose minimum val_rmse for each horizon
        for h in [24, 48, 72]:
            sub = eval_df[eval_df["horizon"] == h]
            selected = best_models[best_models["horizon"] == h].iloc[0]
            assert selected["val_rmse"] == sub["val_rmse"].min()

    def test_evaluate_episode_performance(self, evaluator):
        df, tiers = evaluator.load_and_engineer()
        eval_df = evaluator.evaluate_all_models(df, tiers)
        best_models = evaluator.select_best_models_on_validation(eval_df)
        episode_df = evaluator.evaluate_episode_performance(df, best_models, tiers)

        assert len(episode_df) > 0
        assert "regime" in episode_df.columns
        assert "mbe" in episode_df.columns
        assert "Severe Episode (>= 120 µg/m³)" in episode_df["regime"].values

    def test_evaluate_regimes(self, evaluator):
        df, tiers = evaluator.load_and_engineer()
        eval_df = evaluator.evaluate_all_models(df, tiers)
        best_models = evaluator.select_best_models_on_validation(eval_df)
        regime_df = evaluator.evaluate_regimes(df, best_models, tiers)

        assert len(regime_df) > 0
        assert "regime" in regime_df.columns
        assert "Convective Daytime" in regime_df["regime"].values


class TestEvaluationPlotting:
    def test_plot_actual_vs_predicted(self):
        y_true = np.array([80.0, 120.0, 160.0])
        y_pred = np.array([85.0, 115.0, 150.0])
        fig = plot_actual_vs_predicted(y_true, y_pred, horizon=24, model_name="XGBoost")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # scatter points + 1:1 line

    def test_plot_residuals_diagnostic(self):
        y_true = np.array([80.0, 120.0, 160.0])
        y_pred = np.array([85.0, 115.0, 150.0])
        fig = plot_residuals_diagnostic(y_true, y_pred, horizon=24, model_name="XGBoost")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # histogram + scatter

    def test_plot_model_comparison_bars(self, evaluator):
        df, tiers = evaluator.load_and_engineer()
        eval_df = evaluator.evaluate_all_models(df, tiers)
        fig = plot_model_comparison_bars(eval_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 6  # 3 models * (val + test)

    def test_plot_horizon_error_trajectory(self, evaluator):
        df, tiers = evaluator.load_and_engineer()
        eval_df = evaluator.evaluate_all_models(df, tiers)
        best_models = evaluator.select_best_models_on_validation(eval_df)
        fig = plot_horizon_error_trajectory(best_models)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 4  # val rmse, val mae, test rmse, test mae

    def test_plot_regime_performance(self, evaluator):
        df, tiers = evaluator.load_and_engineer()
        eval_df = evaluator.evaluate_all_models(df, tiers)
        best_models = evaluator.select_best_models_on_validation(eval_df)
        regime_df = evaluator.evaluate_regimes(df, best_models, tiers)
        fig = plot_regime_performance(regime_df)
        assert isinstance(fig, go.Figure)

    def test_plot_severe_episode_errors(self, evaluator):
        df, tiers = evaluator.load_and_engineer()
        eval_df = evaluator.evaluate_all_models(df, tiers)
        best_models = evaluator.select_best_models_on_validation(eval_df)
        episode_df = evaluator.evaluate_episode_performance(df, best_models, tiers)
        fig = plot_severe_episode_errors(episode_df)
        assert isinstance(fig, go.Figure)


class TestEvaluationArtifacts:
    def test_html_figures_exist_and_non_empty(self):
        figures_dir = Path("reports/figures")
        expected_files = [
            "eval_actual_vs_predicted.html",
            "eval_residuals.html",
            "eval_model_comparison.html",
            "eval_horizon_errors.html",
            "eval_regime_performance.html",
            "eval_severe_episodes.html",
        ]
        for fname in expected_files:
            fpath = figures_dir / fname
            assert fpath.exists(), f"Figure missing: {fpath}"
            assert fpath.stat().st_size > 1000

    def test_validation_report_exists_and_populated(self):
        report_path = Path("reports/validation_evaluation_report.md")
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "AtmosCast Model Evaluation & Validation Report" in content
        assert "Selected Best Models by Horizon" in content
        assert "High-Pollution Severe Episode Diagnostics" in content
        assert "Atmospheric Stability & Diurnal Regime Analysis" in content
        assert "Detailed Answers to Core Validation Questions" in content
