"""
Dataset Merger
Aligns and merges cleaned pollution and weather observations by timestamp and station coordinates.
Ensures zero cross-contamination between distinct monitoring sites.
"""

from pathlib import Path
from typing import Optional, Tuple
import logging
import pandas as pd

from src.utils.config import get_project_root

logger = logging.getLogger("AtmosCast.Preprocessing.Merger")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class DatasetMerger:
    """Merges cleaned pollution and meteorological time-series on station_id and timestamp_utc."""

    def __init__(self, processed_dir: Optional[Path] = None):
        self.project_root = get_project_root()
        self.processed_dir = processed_dir or (self.project_root / "data" / "processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def merge_datasets(
        self,
        df_pollution: pd.DataFrame,
        df_weather: pd.DataFrame,
        how: str = "inner",
    ) -> pd.DataFrame:
        """
        Merge cleaned pollution and meteorological observations.
        
        Args:
            df_pollution: Cleaned air quality DataFrame.
            df_weather: Cleaned weather DataFrame.
            how: Join type ('inner' recommended for complete coupled modeling).
            
        Returns:
            pd.DataFrame: Merged coupled dataset.
            
        Raises:
            ValueError: If either DataFrame is empty or missing join keys.
        """
        if df_pollution.empty:
            raise ValueError("Cannot merge: Cleaned pollution DataFrame is empty.")
        if df_weather.empty:
            raise ValueError("Cannot merge: Cleaned weather DataFrame is empty.")

        join_keys = ["station_id", "timestamp_utc"]
        for key in join_keys:
            if key not in df_pollution.columns:
                raise KeyError(f"Pollution DataFrame missing join key '{key}'.")
            if key not in df_weather.columns:
                raise KeyError(f"Weather DataFrame missing join key '{key}'.")

        # Select unique columns from weather to prevent collision
        common_metadata = [
            "station_name",
            "latitude",
            "longitude",
            "timestamp_ist",
            "hour_ist",
            "day_of_week",
            "date_ist",
        ]
        weather_cols_to_add = [
            c for c in df_weather.columns
            if c not in df_pollution.columns or c in join_keys
        ]
        weather_subset = df_weather[weather_cols_to_add].copy()

        logger.info(
            f"Merging pollution ({len(df_pollution)} rows) and weather ({len(df_weather)} rows) "
            f"using '{how}' join on {join_keys}..."
        )

        merged = pd.merge(
            df_pollution,
            weather_subset,
            on=join_keys,
            how=how,
            suffixes=("", "_weather"),
        )

        # Drop any accidental duplicate rows
        initial_merged_len = len(merged)
        merged.drop_duplicates(subset=join_keys, keep="first", inplace=True)
        if len(merged) < initial_merged_len:
            logger.warning(
                f"Removed {initial_merged_len - len(merged)} duplicate timestamp collisions during merge."
            )

        merged.sort_values(by=["station_id", "timestamp_utc"], inplace=True)
        merged.reset_index(drop=True, inplace=True)

        logger.info(
            f"Successfully created coupled dataset with {len(merged)} hourly rows across "
            f"{merged['station_id'].nunique()} monitoring stations."
        )
        return merged

    def save_processed_datasets(
        self,
        df_pollution: pd.DataFrame,
        df_weather: pd.DataFrame,
        df_merged: pd.DataFrame,
        df_qc_log: pd.DataFrame,
    ) -> Tuple[Path, Path, Path, Path]:
        """
        Persist cleaned datasets and QC audit logs into data/processed/.
        
        Returns:
            Tuple[Path, Path, Path, Path]: Paths to saved files.
        """
        poll_path_csv = self.processed_dir / "pollution_cleaned.csv"
        weather_path_csv = self.processed_dir / "weather_cleaned.csv"
        merged_path_csv = self.processed_dir / "merged_delhi_ncr_hourly.csv"
        qc_path_csv = self.processed_dir / "qc_audit_log.csv"

        df_pollution.to_csv(poll_path_csv, index=False)
        df_weather.to_csv(weather_path_csv, index=False)
        df_merged.to_csv(merged_path_csv, index=False)
        df_qc_log.to_csv(qc_path_csv, index=False)

        # Also save parquet if pyarrow is installed for high-performance retrieval
        try:
            df_pollution.to_parquet(self.processed_dir / "pollution_cleaned.parquet", index=False)
            df_weather.to_parquet(self.processed_dir / "weather_cleaned.parquet", index=False)
            df_merged.to_parquet(self.processed_dir / "merged_delhi_ncr_hourly.parquet", index=False)
        except Exception as e:
            logger.info(f"Parquet export skipped or optional: {e}")

        logger.info(f"Saved processed datasets to: {self.processed_dir.resolve()}")
        return poll_path_csv, weather_path_csv, merged_path_csv, qc_path_csv
