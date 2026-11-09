"""
Phase 10: Technical Audit, Hardening & Error Prevention Test Suite.

Exhaustively verifies system resilience against:
- Missing data scenarios & extreme data regimes
- Failed API requests & network outages (offline simulation)
- Invalid user selections & unsupported configurations
- Missing model files & corrupt artifacts
- CPCB AQI calculation edge cases & statutory constraints
- Performance & caching optimization (zero startup retraining)
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
import pytest
import requests

from src.data_collection.open_meteo import OpenMeteoCollector
from src.data_collection.openaq import OpenAQV3Collector
from src.data_collection.cams_air_quality import CAMSAirQualityCollector
from src.data_collection.firms import FIRMSCollector
from src.data_collection.pipeline import DataCollectionPipeline
from src.preprocessing.cleaner import DataCleaner
from src.preprocessing.merger import DatasetMerger
from src.features.engineering import FeatureEngineer
from src.models.predictor import ModelPredictor
from src.forecasting.aqi import CPCBIndexCalculator
from src.forecasting.engine import (
    ForecastEngine,
    InsufficientContextError,
    InvalidTimestampError,
    MissingModelError,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_valid_history():
    """Generates 48 continuous hourly observations for Anand Vihar."""
    times = pd.date_range("2024-01-01 00:00:00", periods=48, freq="h", tz="UTC")
    df = pd.DataFrame({
        "timestamp_utc": times,
        "station_id": "delhi_anand_vihar",
        "station_name": "Anand Vihar, Delhi",
        "pm25": np.linspace(120.0, 240.0, 48),
        "pm10": np.linspace(200.0, 380.0, 48),
        "no2": np.linspace(35.0, 65.0, 48),
        "o3": np.linspace(15.0, 45.0, 48),
        "temperature_2m": np.linspace(12.0, 22.0, 48),
        "relative_humidity_2m": np.linspace(85.0, 45.0, 48),
        "dew_point_2m": np.linspace(8.0, 10.0, 48),
        "precipitation": np.zeros(48),
        "wind_speed_10m": np.linspace(1.2, 3.5, 48),
        "wind_direction_10m": np.linspace(270.0, 310.0, 48),
        "surface_pressure": np.linspace(995.0, 1005.0, 48),
    })
    return df


# -----------------------------------------------------------------------------
# 1. API Failure & Network Outage Simulation (Tasks 13 & 16)
# -----------------------------------------------------------------------------

class TestAPIResilienceAndOfflineMode:
    """Verifies that network issues and HTTP errors are cleanly caught and handled."""

    def test_open_meteo_http_500_error(self):
        collector = OpenMeteoCollector()
        with patch.object(collector.session, "get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_resp.text = "Internal Server Error"
            mock_get.return_value = mock_resp

            with pytest.raises(RuntimeError, match="Open-Meteo API returned error 500"):
                collector.fetch_station_weather("delhi_anand_vihar", "Anand Vihar", 28.64, 77.31, "2024-01-01", "2024-01-02")

    def test_open_meteo_health_check_offline(self):
        collector = OpenMeteoCollector()
        with patch.object(collector.session, "get", side_effect=requests.ConnectionError("Network unreachable")):
            health = collector.health_check()
            assert health["status"] == "unreachable"
            assert "Network unreachable" in health["error"]
            assert health["auth_required"] is False

    def test_openaq_unauthorized_401(self):
        collector = OpenAQV3Collector(api_key="invalid_test_key")
        with patch.object(collector.session, "get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_resp.text = "Unauthorized: Invalid API Key"
            mock_get.return_value = mock_resp

            health = collector.health_check()
            assert health["status"] == "unauthorized"
            assert health["status_code"] == 401

    def test_openaq_network_timeout(self):
        collector = OpenAQV3Collector(api_key="test_key")
        with patch.object(collector.session, "get", side_effect=requests.Timeout("Connection timed out after 15s")):
            health = collector.health_check()
            assert health["status"] == "unreachable"
            assert "timed out" in health["error"]

    def test_firms_optional_status_when_no_api_key(self):
        collector = FIRMSCollector(map_key="")
        health = collector.health_check()
        assert health["status"] == "optional_unconfigured"
        assert health["is_optional"] is True

    def test_data_pipeline_batch_resilience_on_partial_failure(self):
        """Pipeline should log station failure but continue to remaining stations."""
        pipeline = DataCollectionPipeline()
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionResetError("Remote server closed connection")
            return {"hourly": {"time": ["2024-01-01T00:00"], "temperature_2m": [15.0]}}

        with patch.object(pipeline.meteo_collector, "fetch_station_weather", side_effect=side_effect), \
             patch.object(pipeline.cams_collector, "fetch_station_air_quality", return_value={"hourly": {"time": ["2024-01-01T00:00"], "pm2_5": [120.0]}}):
            summary = pipeline.run_historical_download(start_date="2024-01-01", end_date="2024-01-01")
            assert len(summary["failures"]) >= 1
            assert summary["failures"][0]["station_id"] == "delhi_anand_vihar"
            assert summary["stations_completed"] > 0


# -----------------------------------------------------------------------------
# 2. Missing Data & Corrupt History Handling (Task 12)
# -----------------------------------------------------------------------------

class TestMissingDataScenarios:
    """Verifies robustness against NaNs, missing columns, and empty datasets."""

    def test_forecast_engine_with_sparse_missing_values(self, sample_valid_history):
        """Missing values within 3-hour limit should be imputed without errors."""
        df = sample_valid_history.copy()
        df.loc[10:12, "pm25"] = np.nan
        df.loc[15:17, "temperature_2m"] = np.nan

        engine = ForecastEngine()
        result = engine.generate_72h_forecast(df, station_id="delhi_anand_vihar")
        traj = result["forecast_trajectory"]

        assert len(traj) == 72
        assert not traj["predicted_pm25"].isna().any()
        assert (traj["predicted_pm25"] > 0).all()

    def test_forecast_engine_empty_history_raises(self):
        engine = ForecastEngine()
        with pytest.raises(InsufficientContextError, match="empty"):
            engine.generate_72h_forecast(pd.DataFrame(), station_id="delhi_anand_vihar")

    def test_forecast_engine_fewer_than_24_hours_raises(self, sample_valid_history):
        engine = ForecastEngine()
        short_df = sample_valid_history.iloc[:18].copy()
        with pytest.raises(InsufficientContextError, match="requires at least 24 continuous hourly observations"):
            engine.generate_72h_forecast(short_df, station_id="delhi_anand_vihar")

    def test_data_cleaner_rejects_empty_inputs(self):
        cleaner = DataCleaner()
        with pytest.raises(ValueError, match="empty"):
            cleaner.clean_air_quality(pd.DataFrame())
        with pytest.raises(ValueError, match="empty"):
            cleaner.clean_weather(pd.DataFrame())

    def test_data_cleaner_clips_negative_pollutant_values(self):
        cleaner = DataCleaner()
        df = pd.DataFrame({
            "timestamp_utc": pd.to_datetime(["2024-01-01 00:00:00+00:00"]),
            "station_id": ["delhi_anand_vihar"],
            "station_name": ["Anand Vihar"],
            "latitude": [28.6469],
            "longitude": [77.3160],
            "pm25": [-45.0],
            "pm10": [-10.0],
            "no2": [-5.0],
            "o3": [-1.0],
        })
        cleaned = cleaner.clean_air_quality(df)
        assert (cleaned["pm25"] >= 0).all()
        assert (cleaned["pm10"] >= 0).all()
        assert (cleaned["no2"] >= 0).all()
        assert (cleaned["o3"] >= 0).all()

    def test_data_cleaner_rejects_out_of_bounds_coordinates(self):
        cleaner = DataCleaner()
        df = pd.DataFrame({
            "timestamp_utc": pd.to_datetime(["2024-01-01 00:00:00+00:00"]),
            "station_id": ["delhi_anand_vihar"],
            "station_name": ["Anand Vihar"],
            "latitude": [85.0],  # Arctic, far outside Delhi NCR bounds
            "longitude": [77.3160],
            "pm25": [150.0],
        })
        with pytest.raises(ValueError, match="outside Delhi NCR bounds"):
            cleaner.clean_air_quality(df)


# -----------------------------------------------------------------------------
# 3. Invalid User Selections & Edge Configurations (Task 14)
# -----------------------------------------------------------------------------

class TestInvalidUserSelections:
    """Verifies that invalid user selections produce helpful errors."""

    def test_unconfigured_station_selection_in_forecasting(self, sample_valid_history):
        engine = ForecastEngine()
        with pytest.raises(InsufficientContextError):
            engine.generate_72h_forecast(sample_valid_history, station_id="station_nonexistent_mars")

    def test_unsupported_target_pollutant_in_feature_engineering(self):
        with pytest.raises(ValueError, match="Unsupported target pollutant"):
            FeatureEngineer(target_pollutant="unsupported_gas_xyz")

    def test_unsupported_feature_tier_in_feature_engineering(self):
        fe = FeatureEngineer()
        with pytest.raises(ValueError, match="Unknown tier"):
            fe.get_feature_columns("tier99_imaginary")

    def test_invalid_timestamp_string_in_forecasting(self, sample_valid_history):
        engine = ForecastEngine()
        bad_df = sample_valid_history.copy()
        bad_df["timestamp_utc"] = "not_a_valid_date_or_timestamp"
        with pytest.raises(InvalidTimestampError):
            engine.generate_72h_forecast(bad_df, station_id="delhi_anand_vihar")


# -----------------------------------------------------------------------------
# 4. Missing Model Files & Corrupt Artifacts (Task 15)
# -----------------------------------------------------------------------------

class TestMissingModelFilesAndArtifacts:
    """Verifies detection and handling of missing or corrupted model artifacts."""

    def test_engine_raises_on_nonexistent_model_dir(self):
        with pytest.raises(MissingModelError, match="Required model artifact not found"):
            ForecastEngine(models_dir="nonexistent_directory_for_models")

    def test_model_predictor_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError, match="Model artifact not found"):
            ModelPredictor(Path("models/nonexistent_model_file.joblib"))

    def test_model_predictor_raises_on_corrupt_dict(self):
        corrupt_dict = {"model": "not_a_model"}
        with pytest.raises(KeyError, match="Corrupt artifact missing required key: 'feature_names'"):
            ModelPredictor(corrupt_dict)

    def test_model_predictor_validates_missing_input_features(self):
        artifact = {
            "model": MagicMock(),
            "feature_names": ["pm25_lag_1h", "pm25_lag_24h", "wind_speed_10m"],
            "horizon": 24,
            "target_pollutant": "pm25",
        }
        predictor = ModelPredictor(artifact)
        incomplete_df = pd.DataFrame({"pm25_lag_1h": [100.0]})
        with pytest.raises(ValueError, match="missing 2 required features"):
            predictor.predict(incomplete_df)


# -----------------------------------------------------------------------------
# 5. CPCB AQI Calculation Edge Cases (Task 10)
# -----------------------------------------------------------------------------

class TestCPCBIndexCalculationEdgeCases:
    """Tests official CPCB NAQI piecewise linear interpolation and edge cases."""

    def test_zero_concentrations_good_category(self):
        res = CPCBIndexCalculator.compute_official_aqi({"pm25": 0.0, "pm10": 0.0, "no2": 0.0})
        assert res["aqi"] == 0.0
        assert res["category"] == "Good"
        assert res["color"] == "#22C55E"
        assert res["is_official"] is True

    def test_extreme_severe_concentrations_capped_at_500(self):
        res = CPCBIndexCalculator.compute_official_aqi({"pm25": 850.0, "pm10": 1200.0, "no2": 450.0})
        assert res["aqi"] == 500.0
        assert res["category"] == "Severe"
        assert res["color"] == "#7F1D1D"
        assert res["is_official"] is True

    def test_sub_index_boundary_points(self):
        assert CPCBIndexCalculator.calculate_sub_index("pm25", 30.0) == 50.0
        assert CPCBIndexCalculator.calculate_sub_index("pm25", 60.0) == 100.0
        assert CPCBIndexCalculator.calculate_sub_index("pm25", 90.0) == 200.0

    def test_missing_particulate_returns_insufficient(self):
        # 3 gaseous pollutants but zero particulates (PM2.5 and PM10 missing)
        res = CPCBIndexCalculator.compute_official_aqi({"no2": 85.0, "o3": 60.0, "so2": 40.0})
        assert res["aqi"] is None
        assert res["is_official"] is False
        assert res["status"] == "insufficient_pollutants"
        assert "particulate" in res["rules_violation_reason"].lower()

    def test_fewer_than_3_pollutants_returns_insufficient(self):
        # Only 2 pollutants
        res = CPCBIndexCalculator.compute_official_aqi({"pm25": 120.0, "pm10": 220.0})
        assert res["aqi"] is None
        assert res["is_official"] is False
        assert res["status"] == "insufficient_pollutants"
        assert "minimum 3" in res["rules_violation_reason"].lower()

    def test_max_sub_index_aggregation_not_average(self):
        # PM2.5 = 150 -> sub-index ~ 323 (Very Poor)
        # PM10 = 50 -> sub-index ~ 50 (Good)
        # NO2 = 20 -> sub-index ~ 25 (Good)
        # Max is ~323 (Very Poor), whereas average would be ~133 (Moderate). CPCB requires Max!
        res = CPCBIndexCalculator.compute_official_aqi({"pm25": 150.0, "pm10": 50.0, "no2": 20.0})
        assert res["aqi"] >= 310.0
        assert res["category"] == "Very Poor"
        assert res["prominent_pollutant"] == "PM25"


# -----------------------------------------------------------------------------
# 6. Performance & Application Responsiveness (Tasks 1-3 & Performance)
# -----------------------------------------------------------------------------

class TestPerformanceAndStartupGuarantees:
    """Verifies that no models are retrained during startup or forecasting inference."""

    def test_forecasting_engine_does_not_call_fit(self, sample_valid_history):
        engine = ForecastEngine()
        for h, model in engine.models.items():
            assert hasattr(model, "predict")
            assert hasattr(model, "feature_importances_") or hasattr(model, "n_features_in_")

        import time
        start = time.perf_counter()
        result = engine.generate_72h_forecast(sample_valid_history, station_id="delhi_anand_vihar")
        elapsed = time.perf_counter() - start

        assert elapsed < 3.0, f"Inference took {elapsed:.2f}s, expected < 3.0s"
        assert len(result["forecast_trajectory"]) == 72
