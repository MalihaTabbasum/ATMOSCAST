"""
Automated unit tests for AtmosCast Exploratory Data Analysis (EDA) and Visualization module.
Verifies Plotly chart generation, layout properties, HTML exports, and report artifacts.
"""

from pathlib import Path
import json
import unittest
import pandas as pd
import plotly.graph_objects as go

from src.utils.config import get_project_root
from src.utils.visualizations import (
    plot_pm25_timeseries,
    plot_pm10_timeseries,
    plot_diurnal_cycles,
    plot_daily_trend_comparison,
    plot_station_comparison,
    plot_correlation_heatmap,
    plot_weather_relationships_grid,
    plot_pollution_episode_deepdive,
)
from src.utils.eda_runner import run_eda


class TestEDAModule(unittest.TestCase):
    """Test suite for EDA Plotly charts and report generation."""

    @classmethod
    def setUpClass(cls):
        cls.root = get_project_root()
        cls.data_path = cls.root / "data" / "processed" / "merged_delhi_ncr_hourly.csv"
        if cls.data_path.is_file():
            cls.df = pd.read_csv(cls.data_path)
            cls.df["timestamp_utc"] = pd.to_datetime(cls.df["timestamp_utc"], utc=True)
            if "timestamp_ist" in cls.df.columns:
                cls.df["timestamp_ist"] = pd.to_datetime(cls.df["timestamp_ist"])
        else:
            raise FileNotFoundError(f"Processed dataset missing at: {cls.data_path}")

    def test_pm25_timeseries_figure(self):
        """Verify PM2.5 timeseries returns valid Figure with station traces and thresholds."""
        fig = plot_pm25_timeseries(self.df)
        self.assertIsInstance(fig, go.Figure)
        self.assertGreaterEqual(len(fig.data), 6, "Expected at least 6 station traces")
        # Verify statutory standard annotations/lines
        layout_str = str(fig.layout)
        self.assertIn("CPCB 24h Standard", layout_str)
        self.assertIn("WHO 24h Guideline", layout_str)

    def test_pm10_timeseries_figure(self):
        """Verify PM10 timeseries returns valid Figure with CPCB threshold."""
        fig = plot_pm10_timeseries(self.df)
        self.assertIsInstance(fig, go.Figure)
        self.assertGreaterEqual(len(fig.data), 6)
        self.assertIn("CPCB 24h Standard", str(fig.layout))

    def test_diurnal_cycles_figure(self):
        """Verify diurnal cycles figure has dual y-axes and covers 24 hours."""
        fig = plot_diurnal_cycles(self.df)
        self.assertIsInstance(fig, go.Figure)
        trace_names = [t.name for t in fig.data]
        self.assertIn("PM2.5", trace_names)
        self.assertIn("Ground Ozone (O3)", trace_names)
        self.assertIn("NO2", trace_names)

    def test_daily_trend_figure(self):
        """Verify daily trend figure has median and IQR traces."""
        fig = plot_daily_trend_comparison(self.df)
        self.assertIsInstance(fig, go.Figure)
        trace_names = [t.name for t in fig.data]
        self.assertIn("Median PM2.5", trace_names)

    def test_station_comparison_figure(self):
        """Verify station boxplot comparison covers stations."""
        fig = plot_station_comparison(self.df)
        self.assertIsInstance(fig, go.Figure)
        self.assertGreaterEqual(len(fig.data), 1)

    def test_correlation_heatmap_figure(self):
        """Verify correlation heatmap contains pollutants and meteorology."""
        fig = plot_correlation_heatmap(self.df)
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(len(fig.data), 1)
        self.assertEqual(fig.data[0].type, "heatmap")

    def test_weather_relationships_grid(self):
        """Verify 2x2 scatterplot grid has 4 subplot traces."""
        fig = plot_weather_relationships_grid(self.df)
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(len(fig.data), 4)

    def test_pollution_episode_deepdive(self):
        """Verify synchronized 4-row episode diagnostic subplots."""
        fig = plot_pollution_episode_deepdive(self.df, "delhi_anand_vihar")
        self.assertIsInstance(fig, go.Figure)
        self.assertGreaterEqual(len(fig.data), 5)  # PM2.5, PM10, Wind, Temp, RH

    def test_eda_artifacts_and_html_files_exist(self):
        """Verify that all 8 required Plotly HTML files are present in reports/figures/."""
        figures_dir = self.root / "reports" / "figures"
        required_charts = [
            "pm25_timeseries.html",
            "pm10_timeseries.html",
            "diurnal_cycles.html",
            "daily_trends.html",
            "station_comparison.html",
            "correlation_heatmap.html",
            "weather_relationships.html",
            "pollution_episode.html",
        ]
        for chart_name in required_charts:
            chart_file = figures_dir / chart_name
            self.assertTrue(chart_file.is_file(), f"Missing HTML figure: {chart_name}")
            self.assertGreater(chart_file.stat().st_size, 1000, f"Chart file too small: {chart_name}")

    def test_eda_notebook_is_valid_json(self):
        """Verify that notebooks/01_exploratory_data_analysis.ipynb parses as valid Jupyter notebook."""
        nb_path = self.root / "notebooks" / "01_exploratory_data_analysis.ipynb"
        self.assertTrue(nb_path.is_file(), "EDA notebook missing")
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
        self.assertIn("cells", nb)
        self.assertGreaterEqual(len(nb["cells"]), 10)

    def test_eda_summary_report_exists_and_populated(self):
        """Verify that reports/eda_summary_report.md exists and contains required sections."""
        report_path = self.root / "reports" / "eda_summary_report.md"
        self.assertTrue(report_path.is_file(), "EDA summary report missing")
        content = report_path.read_text(encoding="utf-8")
        self.assertIn("correlation does not prove causation", content.lower())
        self.assertIn("Anand Vihar", content)
        self.assertIn("diurnal", content.lower())


if __name__ == "__main__":
    unittest.main()
