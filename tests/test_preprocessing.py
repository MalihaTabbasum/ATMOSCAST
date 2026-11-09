"""
Automated unit and integration tests for AtmosCast Preprocessing Module.
Verifies RawDataLoader, DataCleaner, DatasetMerger, and PreprocessingPipeline.
"""

from pathlib import Path
import unittest
import numpy as np
import pandas as pd

from src.preprocessing.loader import RawDataLoader
from src.preprocessing.cleaner import DataCleaner
from src.preprocessing.merger import DatasetMerger
from src.preprocessing.pipeline import PreprocessingPipeline
from src.utils.config import get_project_root


class TestPreprocessingModule(unittest.TestCase):
    """Test suite for data cleaning, QC verification, and merging."""

    def setUp(self):
        self.root = get_project_root()
        self.cleaner = DataCleaner()
        self.merger = DatasetMerger()

    def test_loader_loads_existing_raw_datasets(self):
        """Verify that loader reads raw data and extracts metadata."""
        loader = RawDataLoader()
        df_aq, aq_units = loader.load_air_quality_data()
        df_weather, w_units = loader.load_weather_data()

        self.assertFalse(df_aq.empty, "Air quality DataFrame is empty")
        self.assertFalse(df_weather.empty, "Weather DataFrame is empty")
        self.assertIn("timestamp_utc", df_aq.columns)
        self.assertIn("station_id", df_aq.columns)
        self.assertIn("timestamp_utc", df_weather.columns)
        self.assertIn("station_id", df_weather.columns)

    def test_cleaner_standardizes_columns_and_timezones(self):
        """Verify column renaming and UTC to IST conversion."""
        sample_aq = pd.DataFrame({
            "timestamp_utc": pd.to_datetime(["2024-01-01 00:00:00+00:00"]),
            "station_id": ["delhi_anand_vihar"],
            "station_name": ["Anand Vihar"],
            "latitude": [28.6469],
            "longitude": [77.3160],
            "pm2_5": [120.0],
            "pm10": [200.0],
            "nitrogen_dioxide": [45.0],
            "ozone": [30.0],
            "sulphur_dioxide": [15.0],
            "carbon_monoxide": [1200.0],  # in µg/m³, should normalize to 1.2 mg/m³
        })
        cleaned = self.cleaner.clean_air_quality(sample_aq)

        # Standardized column names
        self.assertIn("pm25", cleaned.columns)
        self.assertIn("no2", cleaned.columns)
        self.assertIn("o3", cleaned.columns)
        self.assertIn("so2", cleaned.columns)
        self.assertIn("co", cleaned.columns)
        self.assertAlmostEqual(cleaned["co"].iloc[0], 1.2, places=2)

        # IST Timezone fields
        self.assertIn("timestamp_ist", cleaned.columns)
        self.assertIn("hour_ist", cleaned.columns)
        self.assertEqual(cleaned["hour_ist"].iloc[0], 5)  # 00:00 UTC = 05:30 IST -> hour 5

    def test_cleaner_clips_negative_pollutant_values(self):
        """Verify that physically impossible negative concentrations are clipped to 0 and logged."""
        sample_df = pd.DataFrame({
            "timestamp_utc": pd.to_datetime(["2024-01-01 00:00:00+00:00"]),
            "station_id": ["delhi_anand_vihar"],
            "station_name": ["Anand Vihar"],
            "latitude": [28.6469],
            "longitude": [77.3160],
            "pm25": [-15.5],
            "pm10": [50.0],
        })
        cleaner = DataCleaner()
        cleaned = cleaner.clean_air_quality(sample_df)

        self.assertEqual(cleaned["pm25"].iloc[0], 0.0)
        qc_log = cleaner.get_qc_audit_dataframe()
        self.assertFalse(qc_log.empty)
        self.assertEqual(qc_log["event_type"].iloc[0], "negative_concentration")

    def test_cleaner_pm_ratio_sanity(self):
        """Verify that instances where PM2.5 > PM10 are corrected to maintain physical bounds."""
        sample_df = pd.DataFrame({
            "timestamp_utc": pd.to_datetime(["2024-01-01 00:00:00+00:00"]),
            "station_id": ["delhi_anand_vihar"],
            "station_name": ["Anand Vihar"],
            "latitude": [28.6469],
            "longitude": [77.3160],
            "pm25": [180.0],
            "pm10": [120.0],  # PM2.5 > PM10 violation
        })
        cleaner = DataCleaner()
        cleaned = cleaner.clean_air_quality(sample_df)

        self.assertEqual(cleaned["pm10"].iloc[0], 180.0)
        qc_log = cleaner.get_qc_audit_dataframe()
        self.assertTrue((qc_log["event_type"] == "pm_ratio_inversion").any())

    def test_cleaner_rejects_invalid_coordinates(self):
        """Verify that coordinates outside Delhi NCR raise ValueError."""
        out_of_bounds_df = pd.DataFrame({
            "timestamp_utc": pd.to_datetime(["2024-01-01 00:00:00+00:00"]),
            "station_id": ["invalid_location"],
            "station_name": ["Invalid Station"],
            "latitude": [19.0760],  # Mumbai coordinates
            "longitude": [72.8777],
            "pm25": [50.0],
        })
        with self.assertRaises(ValueError):
            self.cleaner.clean_air_quality(out_of_bounds_df)

    def test_leakage_safe_imputation_does_not_leak_future(self):
        """Verify that imputation forward-fills only and does not backward-fill from future."""
        sample_series = pd.DataFrame({
            "timestamp_utc": pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC"),
            "station_id": ["st1"] * 5,
            "val": [np.nan, 10.0, np.nan, np.nan, 50.0],
        })
        cleaner = DataCleaner()
        imputed = cleaner._impute_station_series_leakage_safe(sample_series, cols_to_impute=["val"], max_gap=2)

        # First row cannot be filled from future (must remain NaN)
        self.assertTrue(np.isnan(imputed["val"].iloc[0]))
        # Row 1 is 10.0
        self.assertEqual(imputed["val"].iloc[1], 10.0)
        # Rows 2 and 3 forward filled with 10.0
        self.assertEqual(imputed["val"].iloc[2], 10.0)
        self.assertEqual(imputed["val"].iloc[3], 10.0)
        # Row 4 is 50.0
        self.assertEqual(imputed["val"].iloc[4], 50.0)

    def test_merger_aligns_clean_datasets(self):
        """Verify inner join on station_id and timestamp_utc without cross-station contamination."""
        times = pd.date_range("2024-01-01", periods=3, freq="h", tz="UTC")
        df_aq = pd.DataFrame({
            "timestamp_utc": list(times) + list(times),
            "station_id": ["st1", "st1", "st1", "st2", "st2", "st2"],
            "station_name": ["Station 1"] * 3 + ["Station 2"] * 3,
            "pm25": [10, 20, 30, 40, 50, 60],
        })
        df_weather = pd.DataFrame({
            "timestamp_utc": list(times) + list(times),
            "station_id": ["st1", "st1", "st1", "st2", "st2", "st2"],
            "temperature_2m": [15, 16, 17, 18, 19, 20],
        })
        merged = self.merger.merge_datasets(df_aq, df_weather, how="inner")
        self.assertEqual(len(merged), 6)
        self.assertIn("pm25", merged.columns)
        self.assertIn("temperature_2m", merged.columns)

        # Check st1 values are not mixed with st2
        st1_data = merged[merged["station_id"] == "st1"]
        self.assertEqual(st1_data["pm25"].tolist(), [10, 20, 30])
        self.assertEqual(st1_data["temperature_2m"].tolist(), [15, 16, 17])

    def test_processed_output_files_exist_and_non_empty(self):
        """Verify that data/processed/ contains non-empty processed CSV files."""
        proc_dir = self.root / "data" / "processed"
        required_files = [
            "pollution_cleaned.csv",
            "weather_cleaned.csv",
            "merged_delhi_ncr_hourly.csv",
            "qc_audit_log.csv",
        ]
        for fname in required_files:
            fpath = proc_dir / fname
            self.assertTrue(fpath.is_file(), f"Expected processed file missing: {fname}")
            self.assertGreater(fpath.stat().st_size, 0, f"Processed file is empty: {fname}")


if __name__ == "__main__":
    unittest.main()
