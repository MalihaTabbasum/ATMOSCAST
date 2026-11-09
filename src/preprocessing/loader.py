"""
Raw Data Loader
Discovers, validates, and loads raw air quality and meteorological JSON payloads
from data/raw/ alongside their provenance metadata into structured DataFrames.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import json
import logging
import pandas as pd

from src.utils.config import get_project_root

logger = logging.getLogger("AtmosCast.Preprocessing.Loader")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class RawDataLoader:
    """Loads and standardizes raw ingestion files from data/raw/."""

    def __init__(self, raw_dir: Optional[Path] = None):
        self.project_root = get_project_root()
        self.raw_dir = raw_dir or (self.project_root / "data" / "raw")

        if not self.raw_dir.exists():
            raise FileNotFoundError(
                f"Raw data directory does not exist: {self.raw_dir.resolve()}. "
                "Ensure Phase 2 data collection has been executed."
            )

    def load_air_quality_data(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Scan and load all raw air quality files (CAMS / OpenAQ) in data/raw/.
        
        Returns:
            Tuple[pd.DataFrame, Dict[str, Any]]: Concatenated raw DataFrame and unit mapping.
            
        Raises:
            FileNotFoundError: If no air quality files are found.
            ValueError: If payloads are malformed or empty.
        """
        # Discover air quality JSON files (excluding provenance sidecars)
        aq_files = sorted([
            f for f in self.raw_dir.glob("*.json")
            if not f.name.endswith("_provenance.json") and ("air_quality" in f.name or "openaq" in f.name)
        ])

        if not aq_files:
            raise FileNotFoundError(
                f"No air quality raw datasets found in {self.raw_dir.resolve()}. "
                "Run 'python -m src.data_collection.pipeline --historical' first."
            )

        dfs = []
        combined_units = {}

        for file_path in aq_files:
            prov_file = self.raw_dir / f"{file_path.stem}_provenance.json"
            prov_data = {}
            if prov_file.is_file():
                with open(prov_file, "r", encoding="utf-8") as pf:
                    prov_data = json.load(pf)

            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    payload = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Corrupted JSON in file {file_path.name}: {e}")

            hourly = payload.get("hourly")
            if not hourly or "time" not in hourly:
                logger.warning(f"File {file_path.name} contains no hourly data block. Skipping.")
                continue

            df = pd.DataFrame(hourly)
            if df.empty:
                logger.warning(f"File {file_path.name} has empty hourly table. Skipping.")
                continue

            # Standardize timestamp
            df["timestamp_utc"] = pd.to_datetime(df["time"], utc=True)
            df.drop(columns=["time"], inplace=True)

            # Metadata from provenance or payload
            station_id = prov_data.get("station_id") or self._extract_station_id_from_filename(file_path.name)
            df["station_id"] = station_id
            df["station_name"] = prov_data.get("station_name", station_id)
            df["latitude"] = prov_data.get("latitude") or payload.get("latitude")
            df["longitude"] = prov_data.get("longitude") or payload.get("longitude")
            df["source_file"] = file_path.name

            # Collect units
            units = payload.get("hourly_units", {})
            for k, v in units.items():
                if k != "time":
                    combined_units[k] = v

            dfs.append(df)

        if not dfs:
            raise ValueError(f"All air quality datasets in {self.raw_dir.resolve()} were empty or invalid.")

        combined_df = pd.concat(dfs, ignore_index=True)
        # Deduplicate across overlapping test and historical files
        initial_len = len(combined_df)
        combined_df.drop_duplicates(subset=["station_id", "timestamp_utc"], keep="last", inplace=True)
        logger.info(
            f"Loaded {len(combined_df)} raw air quality records across {combined_df['station_id'].nunique()} stations "
            f"({initial_len - len(combined_df)} duplicates removed)."
        )
        return combined_df, combined_units

    def load_weather_data(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Scan and load all raw Open-Meteo weather files in data/raw/.
        
        Returns:
            Tuple[pd.DataFrame, Dict[str, Any]]: Concatenated raw weather DataFrame and unit mapping.
            
        Raises:
            FileNotFoundError: If no weather files are found.
            ValueError: If payloads are malformed or empty.
        """
        met_files = sorted([
            f for f in self.raw_dir.glob("*.json")
            if not f.name.endswith("_provenance.json") and ("open_meteo" in f.name or "weather" in f.name)
        ])

        if not met_files:
            raise FileNotFoundError(
                f"No weather raw datasets found in {self.raw_dir.resolve()}. "
                "Run 'python -m src.data_collection.pipeline --historical' first."
            )

        dfs = []
        combined_units = {}

        for file_path in met_files:
            prov_file = self.raw_dir / f"{file_path.stem}_provenance.json"
            prov_data = {}
            if prov_file.is_file():
                with open(prov_file, "r", encoding="utf-8") as pf:
                    prov_data = json.load(pf)

            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    payload = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Corrupted JSON in file {file_path.name}: {e}")

            hourly = payload.get("hourly")
            if not hourly or "time" not in hourly:
                logger.warning(f"File {file_path.name} contains no hourly data block. Skipping.")
                continue

            df = pd.DataFrame(hourly)
            if df.empty:
                logger.warning(f"File {file_path.name} has empty hourly table. Skipping.")
                continue

            df["timestamp_utc"] = pd.to_datetime(df["time"], utc=True)
            df.drop(columns=["time"], inplace=True)

            station_id = prov_data.get("station_id") or self._extract_station_id_from_filename(file_path.name)
            df["station_id"] = station_id
            df["station_name"] = prov_data.get("station_name", station_id)
            df["latitude"] = prov_data.get("latitude") or payload.get("latitude")
            df["longitude"] = prov_data.get("longitude") or payload.get("longitude")
            df["elevation"] = prov_data.get("elevation") or payload.get("elevation")
            df["source_file"] = file_path.name

            units = payload.get("hourly_units", {})
            for k, v in units.items():
                if k != "time":
                    combined_units[k] = v

            dfs.append(df)

        if not dfs:
            raise ValueError(f"All weather datasets in {self.raw_dir.resolve()} were empty or invalid.")

        combined_df = pd.concat(dfs, ignore_index=True)
        initial_len = len(combined_df)
        combined_df.drop_duplicates(subset=["station_id", "timestamp_utc"], keep="last", inplace=True)
        logger.info(
            f"Loaded {len(combined_df)} raw weather records across {combined_df['station_id'].nunique()} stations "
            f"({initial_len - len(combined_df)} duplicates removed)."
        )
        return combined_df, combined_units

    @staticmethod
    def _extract_station_id_from_filename(filename: str) -> str:
        """Fallback to extract station id from naming convention (e.g. open_meteo_delhi_anand_vihar_...)."""
        parts = filename.replace(".json", "").split("_")
        if len(parts) >= 4:
            # Reconstruct middle tokens before date strings
            # Example: cams_air_quality_delhi_anand_vihar_2024-01-01_2024-01-07
            clean_parts = [p for p in parts if not p.startswith("202") and p not in ["cams", "air", "quality", "open", "meteo"]]
            return "_".join(clean_parts)
        return filename
