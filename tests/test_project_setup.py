"""
Unit tests for AtmosCast project setup, folder structure, and configuration integrity.
Compatible with both standard `unittest` and `pytest`.
"""

import unittest
from pathlib import Path
import yaml
from src.utils.config import (
    get_project_root,
    load_config,
    get_stations,
    get_pollutants,
    get_forecast_horizons,
)


class TestProjectSetup(unittest.TestCase):
    """Verifies repository structure, configuration files, and utility functions."""

    def setUp(self):
        self.root = get_project_root()

    def test_required_directories_exist(self):
        """Verify that all core project directories exist."""
        required_dirs = [
            "config",
            "data",
            "data/raw",
            "data/processed",
            "data/external",
            "src",
            "src/data_collection",
            "src/preprocessing",
            "src/features",
            "src/models",
            "src/forecasting",
            "src/evaluation",
            "src/explainability",
            "src/utils",
            "notebooks",
            "tests",
            "reports",
            "assets/screenshots",
        ]
        for dir_rel in required_dirs:
            dir_path = self.root / dir_rel
            self.assertTrue(
                dir_path.is_dir(),
                f"Required directory does not exist: {dir_rel}"
            )

    def test_config_settings_yaml_loads(self):
        """Verify settings.yaml exists, is valid YAML, and contains essential root keys."""
        config = load_config()
        self.assertIsInstance(config, dict)
        self.assertIn("project", config)
        self.assertIn("stations", config)
        self.assertIn("pollutants", config)
        self.assertIn("meteorology", config)
        self.assertIn("forecasting", config)
        self.assertIn("api", config)
        self.assertIn("ui", config)

    def test_stations_configuration_validity(self):
        """Ensure stations are defined with valid Delhi NCR geographic coordinates."""
        stations = get_stations()
        self.assertGreaterEqual(len(stations), 4, "Expected at least 4 monitoring stations.")

        # Delhi NCR approx latitude: 28.0 - 29.0, longitude: 76.5 - 77.8
        for st in stations:
            self.assertIn("id", st)
            self.assertIn("name", st)
            self.assertIn("latitude", st)
            self.assertIn("longitude", st)
            self.assertTrue(28.0 <= st["latitude"] <= 29.2, f"Station {st['id']} latitude out of range")
            self.assertTrue(76.5 <= st["longitude"] <= 78.0, f"Station {st['id']} longitude out of range")

    def test_pollutants_configured(self):
        """Ensure primary pollutants PM2.5, PM10, O3, and NO2 are configured."""
        pollutants_cfg = get_pollutants()
        self.assertEqual(pollutants_cfg.get("primary_target"), "PM2.5")
        
        monitored = pollutants_cfg.get("monitored", [])
        codes = {p["code"] for p in monitored}
        required_codes = {"pm25", "pm10", "o3", "no2"}
        self.assertTrue(
            required_codes.issubset(codes),
            f"Missing required pollutant codes. Found: {codes}"
        )

    def test_forecast_horizons(self):
        """Verify 24, 48, and 72-hour forecast horizons are configured."""
        horizons = get_forecast_horizons()
        self.assertEqual(horizons, [24, 48, 72])

    def test_env_example_has_keys(self):
        """Ensure .env.example contains templates for all external API credentials."""
        env_file = self.root / ".env.example"
        self.assertTrue(env_file.is_file(), ".env.example file not found")
        content = env_file.read_text(encoding="utf-8")
        self.assertIn("OPENAQ_API_KEY", content)
        self.assertIn("NASA_FIRMS_MAP_KEY", content)
        self.assertIn("ATMOSCAST_DATA_DIR", content)

    def test_requirements_txt_contains_core_packages(self):
        """Ensure requirements.txt specifies all required libraries."""
        req_file = self.root / "requirements.txt"
        self.assertTrue(req_file.is_file(), "requirements.txt file not found")
        req_text = req_file.read_text(encoding="utf-8").lower()
        core_packages = ["streamlit", "plotly", "pandas", "numpy", "scikit-learn", "xgboost", "shap", "pytest"]
        for pkg in core_packages:
            self.assertIn(pkg, req_text, f"Missing required dependency '{pkg}' in requirements.txt")


if __name__ == "__main__":
    unittest.main()
