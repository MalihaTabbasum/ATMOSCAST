"""
EDA Pipeline Runner
Loads the processed coupled dataset, generates all 8 required interactive Plotly visualizations,
persists interactive HTML charts into reports/figures/, and updates reports/eda_summary_report.md.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging
import pandas as pd

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

logger = logging.getLogger("AtmosCast.EDA.Runner")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def run_eda(
    data_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Run exploratory data analysis and export all Plotly HTML visualizations.
    
    Args:
        data_path: Path to processed merged dataset.
        output_dir: Directory where HTML figures will be written.
        
    Returns:
        Dict[str, Any]: Summary dictionary of generated figures and key statistics.
    """
    root = get_project_root()
    data_path = data_path or (root / "data" / "processed" / "merged_delhi_ncr_hourly.csv")
    output_dir = output_dir or (root / "reports" / "figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not data_path.is_file():
        raise FileNotFoundError(
            f"Processed dataset not found at {data_path.resolve()}. "
            "Ensure Phase 3 preprocessing has completed successfully."
        )

    logger.info(f"Loading coupled dataset from {data_path.resolve()}...")
    df = pd.read_csv(data_path)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    if "timestamp_ist" in df.columns:
        df["timestamp_ist"] = pd.to_datetime(df["timestamp_ist"])

    logger.info(f"Loaded {len(df)} rows across {df['station_id'].nunique()} stations.")

    figures = {
        "pm25_timeseries.html": plot_pm25_timeseries(df),
        "pm10_timeseries.html": plot_pm10_timeseries(df),
        "diurnal_cycles.html": plot_diurnal_cycles(df),
        "daily_trends.html": plot_daily_trend_comparison(df),
        "station_comparison.html": plot_station_comparison(df),
        "correlation_heatmap.html": plot_correlation_heatmap(df),
        "weather_relationships.html": plot_weather_relationships_grid(df),
        "pollution_episode.html": plot_pollution_episode_deepdive(df, "delhi_anand_vihar"),
    }

    generated_paths = {}
    for filename, fig in figures.items():
        file_path = output_dir / filename
        fig.write_html(str(file_path), include_plotlyjs="cdn")
        generated_paths[filename] = str(file_path)
        logger.info(f"Exported interactive chart: {file_path.name}")

    summary = {
        "total_records": len(df),
        "stations_count": df["station_id"].nunique(),
        "start_date": str(df["timestamp_utc"].min()),
        "end_date": str(df["timestamp_utc"].max()),
        "pm25_mean": float(df["pm25"].mean()),
        "pm25_median": float(df["pm25"].median()),
        "pm25_max": float(df["pm25"].max()),
        "pm10_mean": float(df["pm10"].mean()),
        "figures_generated": list(generated_paths.keys()),
        "output_directory": str(output_dir),
    }

    logger.info("EDA visual asset generation completed successfully.")
    return summary


if __name__ == "__main__":
    summary = run_eda()
    print("\n=== EDA Generation Summary ===")
    import json
    print(json.dumps(summary, indent=2))
