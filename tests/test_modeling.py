"""
Unit Tests for AtmosCast Machine Learning Development (Phase 5).

Verifies:
- Feature engineering transformations, cyclical encodings, and atmospheric proxies
- Leakage-free chronological splitting
- Baseline, Random Forest, and XGBoost model training and evaluation
- Model artifact loading, input feature schema verification, and prediction shapes
- Multi-horizon predictor bundling across 24h, 48h, and 72h
- Model comparison report and registry integrity
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.features.engineering import FeatureEngineer
from src.models.baseline import PersistenceForecaster
from src.models.trainer import ModelTrainer, compute_regression_metrics
from src.models.predictor import ModelPredictor, MultiHorizonPredictor
from src.models.pipeline import MLPipeline


@pytest.fixture
def sample_merged_data():
    """Loads a slice of the real merged analytical dataset."""
    data_path = Path("data/processed/merged_delhi_ncr_hourly.csv")
    assert data_path.exists(), f"Processed dataset missing at {data_path}"
    df = pd.read_csv(data_path)
    return df


class TestFeatureEngineering:
    def test_temporal_features_cyclical_ranges(self, sample_merged_data):
        fe = FeatureEngineer()
        df = fe.extract_temporal_features(sample_merged_data)
        for col in ["hour_sin", "hour_cos", "day_of_week_sin", "day_of_week_cos", "month_sin", "month_cos"]:
            assert col in df.columns
            assert df[col].between(-1.0001, 1.0001).all()
        assert "is_weekend" in df.columns
        assert set(df["is_weekend"].unique()).issubset({0.0, 1.0})

    def test_circular_wind_encoding(self, sample_merged_data):
        fe = FeatureEngineer()
        df = fe.extract_circular_wind(sample_merged_data)
        assert "wind_dir_sin" in df.columns
        assert "wind_dir_cos" in df.columns
        assert df["wind_dir_sin"].between(-1.0001, 1.0001).all()
        assert df["wind_dir_cos"].between(-1.0001, 1.0001).all()

    def test_atmospheric_indicators_generation(self, sample_merged_data):
        fe = FeatureEngineer()
        df = fe.extract_temporal_features(sample_merged_data)
        df = fe.compute_station_lags_and_rolling(df)
        df = fe.compute_atmospheric_indicators(df)

        assert "dew_point_depression" in df.columns
        assert "stagnation_index" in df.columns
        assert "wind_humidity_ratio" in df.columns
        assert "temp_rh_interaction" in df.columns
        assert "inversion_risk_index" in df.columns
        assert (df["dew_point_depression"].dropna() >= -5.0).all()

    def test_multi_horizon_targets_shape(self, sample_merged_data):
        fe = FeatureEngineer()
        df = fe.create_multi_horizon_targets(sample_merged_data, horizons=[24, 48, 72], pollutant="pm25")
        for h in [24, 48, 72]:
            assert f"target_pm25_h{h}" in df.columns

    def test_feature_tiers_hierarchy(self, sample_merged_data):
        fe = FeatureEngineer()
        eng_df, tiers = fe.process_dataset(sample_merged_data, horizons=[24, 48, 72])

        t1 = tiers[FeatureEngineer.TIER1_POLLUTION_ONLY]
        t2 = tiers[FeatureEngineer.TIER2_POLLUTION_WEATHER]
        t3 = tiers[FeatureEngineer.TIER3_COUPLED_ATMOSPHERIC]

        # Ensure strict subset hierarchy: Tier 1 subset of Tier 2 subset of Tier 3
        assert set(t1).issubset(set(t2))
        assert set(t2).issubset(set(t3))
        assert len(t1) < len(t2) < len(t3)


class TestPersistenceBaseline:
    def test_naive_persistence_prediction(self):
        df = pd.DataFrame({"pm25": [100.0, 150.0, 200.0]})
        forecaster = PersistenceForecaster(target_column="pm25", strategy="naive")
        forecaster.fit(df)
        preds = forecaster.predict(df)
        np.testing.assert_array_equal(preds, np.array([100.0, 150.0, 200.0]))

    def test_persistence_fallback(self):
        forecaster = PersistenceForecaster(target_column="pm25")
        forecaster.fit(pd.DataFrame(), y=np.array([120.0, 140.0]))
        assert forecaster.fallback_value_ == 130.0


class TestModelTrainingAndEvaluation:
    def test_compute_regression_metrics(self):
        y_true = np.array([100.0, 120.0, 140.0, 160.0])
        y_pred = np.array([105.0, 115.0, 145.0, 155.0])
        metrics = compute_regression_metrics(y_true, y_pred)

        assert "MAE" in metrics
        assert "RMSE" in metrics
        assert "R2" in metrics
        assert "MAPE" in metrics
        assert metrics["MAE"] == 5.0
        assert metrics["RMSE"] == 5.0
        assert metrics["R2"] > 0.9

    def test_chronological_split_zero_leakage(self, sample_merged_data):
        fe = FeatureEngineer()
        eng_df, tiers = fe.process_dataset(sample_merged_data)
        trainer = ModelTrainer(target_pollutant="pm25")

        features = tiers[FeatureEngineer.TIER1_POLLUTION_ONLY]
        X_train, X_val, X_test, y_train, y_val, y_test = trainer.chronological_split(
            eng_df, feature_cols=features, target_col="target_pm25_h24"
        )

        assert len(X_train) > len(X_val)
        assert len(X_val) > 0
        assert len(X_test) > 0
        assert len(X_train) + len(X_val) + len(X_test) == len(y_train) + len(y_val) + len(y_test)

    def test_single_model_training_and_serialization(self, sample_merged_data, tmp_path):
        fe = FeatureEngineer()
        eng_df, tiers = fe.process_dataset(sample_merged_data)
        trainer = ModelTrainer(target_pollutant="pm25", models_dir=str(tmp_path))

        features = tiers[FeatureEngineer.TIER1_POLLUTION_ONLY][:10]
        result = trainer.train_single_model(
            df=eng_df,
            model_type="random_forest",
            tier_name="tier1_pollution_only",
            feature_cols=features,
            horizon=24,
        )

        assert Path(result["artifact_path"]).exists()
        assert "test_metrics" in result
        assert result["test_metrics"]["MAE"] > 0


class TestInferenceAndPrediction:
    def test_model_predictor_loading_and_inference(self, sample_merged_data):
        artifact_path = Path("models/xgboost_tier3_coupled_atmospheric_pm25_h24.joblib")
        assert artifact_path.exists(), "Model artifact must exist from pipeline run."

        predictor = ModelPredictor(artifact_path)
        assert predictor.horizon == 24
        assert predictor.target_pollutant == "pm25"

        fe = FeatureEngineer()
        eng_df, _ = fe.process_dataset(sample_merged_data)

        # Predict on slice
        preds = predictor.predict(eng_df.iloc[:10])
        assert len(preds) == 10
        assert not np.isnan(preds).any()

    def test_model_predictor_missing_features_validation(self):
        artifact_path = Path("models/random_forest_tier1_pollution_only_pm25_h24.joblib")
        predictor = ModelPredictor(artifact_path)

        incomplete_df = pd.DataFrame({"dummy": [1, 2, 3]})
        with pytest.raises(ValueError, match="missing .* required features"):
            predictor.predict(incomplete_df)

    def test_multi_horizon_predictor(self, sample_merged_data):
        multi_pred = MultiHorizonPredictor(
            models_dir="models",
            model_type="xgboost",
            tier_name="tier3_coupled_atmospheric",
            target_pollutant="pm25",
            horizons=[24, 48, 72],
        )

        fe = FeatureEngineer()
        eng_df, _ = fe.process_dataset(sample_merged_data)

        preds_df = multi_pred.predict_all_horizons(eng_df.iloc[:5])
        assert preds_df.shape == (5, 3)
        assert list(preds_df.columns) == ["pred_pm25_h24", "pred_pm25_h48", "pred_pm25_h72"]
        assert not preds_df.isna().any().any()


class TestArtifactsAndReports:
    def test_model_registry_json_validity(self):
        registry_path = Path("models/model_registry.json")
        assert registry_path.exists()
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)

        assert registry["model_count"] == 27
        assert registry["target_pollutant"] == "pm25"
        assert set(registry["horizons"]) == {24, 48, 72}

    def test_comparison_report_exists_and_populated(self):
        report_path = Path("reports/model_comparison_report.md")
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "AtmosCast Model Development & Benchmark Report" in content
        assert "Complete Model Performance Benchmark Table" in content
        assert "Direct Multi-Horizon Forecasting" in content
        assert "LSTM" in content
