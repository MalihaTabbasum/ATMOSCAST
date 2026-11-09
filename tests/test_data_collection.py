"""
Unit and integration tests for AtmosCast Data Collection module.
Verifies BaseDataCollector, OpenMeteoCollector, OpenAQV3Collector,
CAMSAirQualityCollector, FIRMSCollector, and DataCollectionPipeline.
"""

import json
import unittest
from pathlib import Path
import pandas as pd

from src.data_collection.base import BaseDataCollector
from src.data_collection.open_meteo import OpenMeteoCollector
from src.data_collection.openaq import OpenAQV3Collector
from src.data_collection.cams_air_quality import CAMSAirQualityCollector
from src.data_collection.firms import FIRMSCollector
from src.data_collection.pipeline import DataCollectionPipeline
from src.utils.config import get_project_root


class DummyCollector(BaseDataCollector):
    """Concrete implementation for testing BaseDataCollector functionality."""
    def __init__(self):
        super().__init__(source_name="DummyTest")

    def health_check(self):
        return {"status": "ok"}


class TestDataCollection(unittest.TestCase):
    """Test suite for data collection components."""

    def setUp(self):
        self.root = get_project_root()
        self.raw_dir = self.root / "data" / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def test_base_collector_provenance_and_saving(self):
        """Verify that save_raw_payload writes both payload and provenance sidecar."""
        collector = DummyCollector()
        sample_payload = {"test_metric": [1, 2, 3]}
        sample_prov = {"station_id": "test_station", "units": "µg/m³"}
        filename = "test_sample_output.json"

        target_file = collector.save_raw_payload(sample_payload, filename, sample_prov)
        self.assertTrue(target_file.is_file(), "Raw payload file not written")

        prov_file = self.raw_dir / f"{target_file.stem}_provenance.json"
        self.assertTrue(prov_file.is_file(), "Provenance sidecar file not written")

        with open(prov_file, "r", encoding="utf-8") as f:
            prov_data = json.load(f)
            self.assertEqual(prov_data["station_id"], "test_station")
            self.assertEqual(prov_data["collector"], "DummyTest")
            self.assertIn("retrieved_at_utc", prov_data)

        # Cleanup test files
        target_file.unlink(missing_ok=True)
        prov_file.unlink(missing_ok=True)

    def test_open_meteo_raw_to_dataframe(self):
        """Verify parsing of Open-Meteo payload into structured DataFrame."""
        mock_payload = {
            "latitude": 28.6469,
            "longitude": 77.3160,
            "hourly": {
                "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
                "temperature_2m": [12.5, 13.0],
                "relative_humidity_2m": [80, 75],
                "wind_speed_10m": [5.0, 6.2],
            },
        }
        df = OpenMeteoCollector.raw_to_dataframe(mock_payload, "delhi_anand_vihar")
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertIn("timestamp_utc", df.columns)
        self.assertIn("station_id", df.columns)
        self.assertIn("temperature_2m", df.columns)
        self.assertEqual(df["station_id"].iloc[0], "delhi_anand_vihar")

    def test_cams_raw_to_dataframe(self):
        """Verify parsing of CAMS air quality payload into structured DataFrame."""
        mock_payload = {
            "latitude": 28.6469,
            "longitude": 77.3160,
            "hourly": {
                "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
                "pm2_5": [180.5, 195.2],
                "pm10": [290.0, 310.5],
                "nitrogen_dioxide": [45.2, 52.0],
            },
        }
        df = CAMSAirQualityCollector.raw_to_dataframe(mock_payload, "delhi_anand_vihar")
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertIn("timestamp_utc", df.columns)
        self.assertIn("pm2_5", df.columns)
        self.assertEqual(df["pm2_5"].iloc[1], 195.2)

    def test_openaq_headers_and_health_check(self):
        """Ensure OpenAQ client builds headers correctly and returns informative message when unauthenticated."""
        collector = OpenAQV3Collector(api_key=None)
        headers = collector._get_headers()
        self.assertIn("User-Agent", headers)
        self.assertNotIn("X-API-Key", headers)

        health = collector.health_check()
        self.assertEqual(health["status"], "authentication_required")
        self.assertFalse(health["auth_configured"])

        # With key
        collector_with_key = OpenAQV3Collector(api_key="mock_secret_key")
        headers_with_key = collector_with_key._get_headers()
        self.assertEqual(headers_with_key.get("X-API-Key"), "mock_secret_key")

    def test_firms_optional_status(self):
        """Ensure FIRMS collector behaves gracefully as an optional source when MAP_KEY is not set."""
        collector = FIRMSCollector(map_key=None)
        health = collector.health_check()
        self.assertEqual(health["status"], "optional_unconfigured")
        self.assertTrue(health["is_optional"])

        # Fetch returns empty DataFrame when unconfigured
        df = collector.fetch_active_fires(date_str="2024-01-01")
        self.assertTrue(df.empty)

    def test_pipeline_audit_all_sources(self):
        """Verify that pipeline audit queries all 4 sources and returns valid audit dict."""
        pipeline = DataCollectionPipeline()
        audit = pipeline.audit_all_sources()
        self.assertIn("timestamp_utc", audit)
        self.assertIn("sources", audit)
        self.assertIn("open_meteo", audit["sources"])
        self.assertIn("cams_air_quality", audit["sources"])
        self.assertIn("openaq_v3", audit["sources"])
        self.assertIn("nasa_firms", audit["sources"])


if __name__ == "__main__":
    unittest.main()
