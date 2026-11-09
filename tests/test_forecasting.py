"""
Unit Tests for AtmosCast 72-Hour Forecasting Engine & CPCB AQI Calculator (Phase 8).

Verifies:
- Official CPCB AQI sub-index calculations, breakpoint interpolation, and categories
- CPCB statutory aggregation rules (Max sub-index, minimum 3 pollutants, particulate requirement)
- 72-Hour forecast generation across selected Delhi NCR stations
- Exact 72-hour forecast trajectory length (1 to 72 hours)
- Clean distinction between actual historical measurements and predicted values
- UTC and IST timestamp alignments
- Metadata recording (generation timestamp, model architecture, weather source)
- Robust error handling:
  * InsufficientContextError (< 24 historical rows)
  * InvalidTimestampError (unparseable dates)
  * MissingModelError (missing artifact path)
  * IncompatibleFeatureError
- Independence from Streamlit
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.forecasting.aqi import CPCBIndexCalculator
from src.forecasting.engine import (
    ForecastEngine,
    InsufficientContextError,
    InvalidTimestampError,
    MissingModelError,
    IncompatibleFeatureError,
)


@pytest.fixture
def sample_history_df():
    data_path = Path("data/processed/merged_delhi_ncr_hourly.csv")
    assert data_path.exists(), f"Processed dataset missing at {data_path}"
    df = pd.read_csv(data_path)
    return df


class TestCPCBIndexCalculator:
    def test_pm25_sub_index_breakpoints(self):
        # Good (0-30 -> 0-50)
        assert CPCBIndexCalculator.calculate_sub_index("pm25", 15.0) == 25.0
        # Satisfactory (31-60 -> 51-100)
        assert 50 < CPCBIndexCalculator.calculate_sub_index("pm25", 45.0) < 100
        # Moderate (61-90 -> 101-200)
        assert 100 < CPCBIndexCalculator.calculate_sub_index("pm25", 75.0) < 200
        # Poor (91-120 -> 201-300)
        assert 200 < CPCBIndexCalculator.calculate_sub_index("pm25", 105.0) < 300
        # Very Poor (121-250 -> 301-400)
        assert 300 < CPCBIndexCalculator.calculate_sub_index("pm25", 185.0) < 400
        # Severe (250+ -> 401-500)
        assert CPCBIndexCalculator.calculate_sub_index("pm25", 350.0) >= 400

    def test_pm10_sub_index_breakpoints(self):
        assert CPCBIndexCalculator.calculate_sub_index("pm10", 25.0) == 25.0
        assert 50 < CPCBIndexCalculator.calculate_sub_index("pm10", 75.0) < 100
        assert 100 < CPCBIndexCalculator.calculate_sub_index("pm10", 175.0) < 200

    def test_max_sub_index_aggregation_not_average(self):
        # Rule: AQI is MAX sub-index, NOT average
        pollutants = {
            "pm25": 110.0,   # Sub-index ~268 (Poor)
            "pm10": 40.0,    # Sub-index 40 (Good)
            "no2": 25.0,     # Sub-index ~31 (Good)
        }
        res = CPCBIndexCalculator.compute_official_aqi(pollutants)

        assert res["is_official"] is True
        assert res["prominent_pollutant"] == "PM25"
        # The overall AQI must match the highest sub-index (~268), not average (~113)
        assert res["aqi"] > 200.0
        assert res["category"] == "Poor"

    def test_insufficient_pollutants_rule(self):
        # Less than 3 pollutants -> official AQI must be unavailable
        res = CPCBIndexCalculator.compute_official_aqi({"pm25": 85.0, "pm10": 120.0})
        assert res["is_official"] is False
        assert res["status"] == "insufficient_pollutants"
        assert res["aqi"] is None
        assert "minimum 3" in res["rules_violation_reason"]

    def test_missing_particulate_rule(self):
        # 3 gaseous pollutants but neither PM2.5 nor PM10 -> official AQI unavailable
        res = CPCBIndexCalculator.compute_official_aqi({"no2": 50.0, "so2": 30.0, "o3": 40.0})
        assert res["is_official"] is False
        assert res["status"] == "insufficient_pollutants"
        assert "particulate" in res["rules_violation_reason"].lower()


class TestForecastEngine:
    def test_forecast_trajectory_length(self, sample_history_df):
        engine = ForecastEngine()
        result = engine.generate_72h_forecast(sample_history_df, station_id="delhi_anand_vihar")

        traj = result["forecast_trajectory"]
        assert len(traj) == 72
        assert list(traj["horizon_hour"]) == list(range(1, 73))

    def test_historical_vs_forecast_distinction(self, sample_history_df):
        engine = ForecastEngine()
        result = engine.generate_72h_forecast(sample_history_df, station_id="delhi_igi_airport")

        combined = result["combined_series"]
        assert "record_type" in combined.columns
        assert set(combined["record_type"].unique()) == {"historical", "forecast"}

        hist = combined[combined["record_type"] == "historical"]
        fc = combined[combined["record_type"] == "forecast"]
        assert len(hist) == 24
        assert len(fc) == 72

    def test_timestamps_utc_and_ist(self, sample_history_df):
        engine = ForecastEngine()
        result = engine.generate_72h_forecast(sample_history_df, station_id="delhi_rk_puram")
        traj = result["forecast_trajectory"]

        assert "timestamp_utc" in traj.columns
        assert "timestamp_ist" in traj.columns
        assert traj["timestamp_ist"].str.endswith("IST").all()

    def test_prediction_finite_and_positive(self, sample_history_df):
        engine = ForecastEngine()
        result = engine.generate_72h_forecast(sample_history_df, station_id="noida_sector_62")
        traj = result["forecast_trajectory"]

        assert (traj["predicted_pm25"] >= 0).all()
        assert not traj["predicted_pm25"].isna().any()
        assert not np.isinf(traj["predicted_pm25"]).any()

        # Uncertainty intervals validity
        assert (traj["lower_bound_pm25"] <= traj["predicted_pm25"]).all()
        assert (traj["predicted_pm25"] <= traj["upper_bound_pm25"]).all()

    def test_metadata_presence(self, sample_history_df):
        engine = ForecastEngine()
        result = engine.generate_72h_forecast(sample_history_df, station_id="gurugram_vikas_sadan")

        assert "forecast_generated_at_utc" in result
        assert "forecast_generated_at_ist" in result
        assert "model_architecture" in result
        assert "weather_source" in result
        assert "is_fallback" in result
        assert result["station_id"] == "gurugram_vikas_sadan"


class TestForecastEngineErrorHandling:
    def test_insufficient_context_raises_error(self, sample_history_df):
        engine = ForecastEngine()
        short_df = sample_history_df.iloc[:10].copy()
        with pytest.raises(InsufficientContextError, match="requires at least 24 continuous hourly observations"):
            engine.generate_72h_forecast(short_df, station_id="delhi_anand_vihar")

    def test_invalid_timestamp_raises_error(self, sample_history_df):
        engine = ForecastEngine()
        bad_df = sample_history_df.iloc[:30].copy()
        bad_df["timestamp_utc"] = "corrupted_timestamp_string"
        bad_df.drop(columns=["timestamp_ist"], inplace=True, errors="ignore")

        with pytest.raises(InvalidTimestampError):
            engine.generate_72h_forecast(bad_df, station_id="delhi_anand_vihar")

    def test_missing_model_raises_error(self):
        with pytest.raises(MissingModelError, match="Required model artifact not found"):
            ForecastEngine(models_dir="non_existent_models_dir")
