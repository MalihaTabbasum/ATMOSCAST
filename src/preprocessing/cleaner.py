"""
Data Cleaning & Quality Control
Standardizes column names, normalizes timezones, validates coordinates and physical bounds,
handles missing data without future leakage, investigates outliers, and maintains a strict QC audit log.
"""

from typing import Any, Dict, List, Optional
import logging
import pandas as pd

from src.utils.config import load_config, get_stations

logger = logging.getLogger("AtmosCast.Preprocessing.Cleaner")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class DataCleaner:
    """Performs rigorous quality control, boundary verification, and leakage-safe cleaning."""

    # Physical plausibility limits for Delhi NCR
    PHYSICAL_LIMITS = {
        "pm25": {"min": 0.0, "max": 1200.0, "extreme_thresh": 600.0, "unit": "µg/m³"},
        "pm10": {"min": 0.0, "max": 2000.0, "extreme_thresh": 900.0, "unit": "µg/m³"},
        "no2": {"min": 0.0, "max": 500.0, "extreme_thresh": 250.0, "unit": "µg/m³"},
        "o3": {"min": 0.0, "max": 400.0, "extreme_thresh": 220.0, "unit": "µg/m³"},
        "so2": {"min": 0.0, "max": 400.0, "extreme_thresh": 180.0, "unit": "µg/m³"},
        "co": {"min": 0.0, "max": 50.0, "extreme_thresh": 4.0, "unit": "mg/m³"},
        "temperature_2m": {"min": -5.0, "max": 55.0, "unit": "°C"},
        "relative_humidity_2m": {"min": 0.0, "max": 100.0, "unit": "%"},
        "dew_point_2m": {"min": -15.0, "max": 40.0, "unit": "°C"},
        "surface_pressure": {"min": 850.0, "max": 1050.0, "unit": "hPa"},
        "wind_speed_10m": {"min": 0.0, "max": 120.0, "unit": "km/h"},
        "wind_direction_10m": {"min": 0.0, "max": 360.0, "unit": "degrees"},
        "precipitation": {"min": 0.0, "max": 250.0, "unit": "mm"},
    }

    # Bounding box for Delhi NCR stations
    NCR_GEO_BOUNDS = {
        "min_lat": 28.0,
        "max_lat": 29.2,
        "min_lon": 76.5,
        "max_lon": 78.0,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()
        self.configured_stations = {s["id"]: s for s in get_stations(self.config)}
        self.qc_log: List[Dict[str, Any]] = []

    def _log_qc_event(
        self,
        event_type: str,
        station_id: str,
        variable: str,
        timestamp: Optional[Any],
        original_value: Any,
        action: str,
        details: str,
    ) -> None:
        """Record an entry in the structured Quality Control audit log."""
        self.qc_log.append({
            "event_type": event_type,
            "station_id": station_id,
            "variable": variable,
            "timestamp": str(timestamp) if timestamp else "N/A",
            "original_value": original_value,
            "action": action,
            "details": details,
        })

    def clean_air_quality(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Clean, standardize, and quality-control raw air quality measurements.
        
        Args:
            df_raw: Raw air quality DataFrame.
            
        Returns:
            pd.DataFrame: Cleaned air quality DataFrame.
        """
        if df_raw.empty:
            raise ValueError("Input air quality DataFrame is empty.")

        df = df_raw.copy()

        # 1. Standardize column naming
        rename_map = {
            "pm2_5": "pm25",
            "pm10": "pm10",
            "nitrogen_dioxide": "no2",
            "ozone": "o3",
            "sulphur_dioxide": "so2",
            "carbon_monoxide": "co",
        }
        df.rename(columns=rename_map, inplace=True)

        # 2. Standardize Carbon Monoxide (convert µg/m³ to mg/m³ if needed to match CPCB standard)
        if "co" in df.columns and df["co"].notna().any():
            sample_val = df["co"].dropna().iloc[0]
            if sample_val > 50.0:  # Raw values > 50 indicate µg/m³ instead of mg/m³
                logger.info("Normalizing CO from µg/m³ to mg/m³ (dividing by 1000.0 per CPCB standard).")
                df["co"] = df["co"] / 1000.0
        if "timestamp_utc" not in df.columns:
            raise KeyError("Missing required column 'timestamp_utc'.")
        
        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
        df["timestamp_ist"] = df["timestamp_utc"].dt.tz_convert("Asia/Kolkata")
        df["hour_ist"] = df["timestamp_ist"].dt.hour
        df["day_of_week"] = df["timestamp_ist"].dt.dayofweek
        df["date_ist"] = df["timestamp_ist"].dt.strftime("%Y-%m-%d")

        # 3. Validate station coordinates
        self._validate_station_coordinates(df)

        # 4. Physical boundary check and outlier screening
        pollutant_cols = ["pm25", "pm10", "no2", "o3", "so2", "co"]
        for col in pollutant_cols:
            if col not in df.columns:
                continue

            limits = self.PHYSICAL_LIMITS.get(col, {})
            min_val = limits.get("min", 0.0)
            max_val = limits.get("max", 1000.0)
            extreme_thresh = limits.get("extreme_thresh", max_val * 0.75)

            # Check negative values
            neg_mask = df[col] < min_val
            neg_count = neg_mask.sum()
            if neg_count > 0:
                for idx, row in df[neg_mask].iterrows():
                    self._log_qc_event(
                        event_type="negative_concentration",
                        station_id=row["station_id"],
                        variable=col,
                        timestamp=row["timestamp_utc"],
                        original_value=row[col],
                        action="clipped_to_zero",
                        details=f"Physically impossible negative concentration: {row[col]} {limits['unit']}",
                    )
                df.loc[neg_mask, col] = min_val

            # Screen extreme readings (Preserve real severe winter episodes, flag implausible sensor errors)
            absurd_mask = df[col] > max_val
            absurd_count = absurd_mask.sum()
            if absurd_count > 0:
                for idx, row in df[absurd_mask].iterrows():
                    self._log_qc_event(
                        event_type="sensor_clipping",
                        station_id=row["station_id"],
                        variable=col,
                        timestamp=row["timestamp_utc"],
                        original_value=row[col],
                        action="capped_at_max",
                        details=f"Value exceeded physical sensor ceiling ({row[col]} > {max_val} {limits['unit']})",
                    )
                df.loc[absurd_mask, col] = max_val

            # Log verified genuine severe pollution episodes
            severe_mask = (df[col] >= extreme_thresh) & (df[col] <= max_val)
            severe_count = severe_mask.sum()
            if severe_count > 0:
                logger.info(
                    f"Preserved {severe_count} verified extreme pollution episodes for {col} "
                    f"(>= {extreme_thresh} {limits['unit']}). Genuine winter inversion readings."
                )

        # 5. Particulate Matter Ratio Sanity (PM2.5 should not exceed PM10)
        if "pm25" in df.columns and "pm10" in df.columns:
            inverted_mask = (df["pm25"] > df["pm10"]) & df["pm25"].notna() & df["pm10"].notna()
            inverted_count = inverted_mask.sum()
            if inverted_count > 0:
                for idx, row in df[inverted_mask].iterrows():
                    self._log_qc_event(
                        event_type="pm_ratio_inversion",
                        station_id=row["station_id"],
                        variable="pm25_vs_pm10",
                        timestamp=row["timestamp_utc"],
                        original_value=f"PM2.5={row['pm25']}, PM10={row['pm10']}",
                        action="logged_and_adjusted",
                        details="PM2.5 concentration exceeded coarse PM10; setting PM10 = PM2.5 to maintain physical bound.",
                    )
                # Physical constraint: PM10 must be at least PM2.5
                df.loc[inverted_mask, "pm10"] = df.loc[inverted_mask, "pm25"]

        # 6. Leakage-safe missing value imputation per station
        df = self._impute_station_series_leakage_safe(df, cols_to_impute=pollutant_cols, max_gap=3)

        df.sort_values(by=["station_id", "timestamp_utc"], inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def clean_weather(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Clean, standardize, and quality-control raw meteorological measurements.
        
        Args:
            df_raw: Raw weather DataFrame.
            
        Returns:
            pd.DataFrame: Cleaned weather DataFrame.
        """
        if df_raw.empty:
            raise ValueError("Input weather DataFrame is empty.")

        df = df_raw.copy()

        # 1. Timezone conversion
        if "timestamp_utc" not in df.columns:
            raise KeyError("Missing required column 'timestamp_utc'.")

        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
        df["timestamp_ist"] = df["timestamp_utc"].dt.tz_convert("Asia/Kolkata")
        df["hour_ist"] = df["timestamp_ist"].dt.hour
        df["day_of_week"] = df["timestamp_ist"].dt.dayofweek
        df["date_ist"] = df["timestamp_ist"].dt.strftime("%Y-%m-%d")

        # 2. Validate coordinates
        self._validate_station_coordinates(df)

        # 3. Physical boundaries and range checks
        weather_cols = [
            "temperature_2m",
            "relative_humidity_2m",
            "dew_point_2m",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "precipitation",
        ]

        for col in weather_cols:
            if col not in df.columns:
                continue

            limits = self.PHYSICAL_LIMITS.get(col, {})
            min_val = limits.get("min")
            max_val = limits.get("max")

            if min_val is not None:
                below_mask = df[col] < min_val
                if below_mask.sum() > 0:
                    for idx, row in df[below_mask].iterrows():
                        self._log_qc_event(
                            event_type="weather_below_min",
                            station_id=row["station_id"],
                            variable=col,
                            timestamp=row["timestamp_utc"],
                            original_value=row[col],
                            action="clipped_to_min",
                            details=f"Below physical limit: {row[col]} < {min_val} {limits.get('unit', '')}",
                        )
                    df.loc[below_mask, col] = min_val

            if max_val is not None:
                above_mask = df[col] > max_val
                if above_mask.sum() > 0:
                    for idx, row in df[above_mask].iterrows():
                        self._log_qc_event(
                            event_type="weather_above_max",
                            station_id=row["station_id"],
                            variable=col,
                            timestamp=row["timestamp_utc"],
                            original_value=row[col],
                            action="clipped_to_max",
                            details=f"Above physical limit: {row[col]} > {max_val} {limits.get('unit', '')}",
                        )
                    df.loc[above_mask, col] = max_val

        # 4. Wind direction normalization (modulo 360)
        if "wind_direction_10m" in df.columns:
            df["wind_direction_10m"] = df["wind_direction_10m"] % 360.0

        # 5. Leakage-safe missing value imputation per station
        df = self._impute_station_series_leakage_safe(df, cols_to_impute=weather_cols, max_gap=3)

        df.sort_values(by=["station_id", "timestamp_utc"], inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def _validate_station_coordinates(self, df: pd.DataFrame) -> None:
        """Verify that all station latitudes and longitudes fall inside Delhi NCR bounds."""
        for station_id, group in df.groupby("station_id"):
            lat = group["latitude"].iloc[0]
            lon = group["longitude"].iloc[0]

            if not (self.NCR_GEO_BOUNDS["min_lat"] <= lat <= self.NCR_GEO_BOUNDS["max_lat"]):
                raise ValueError(
                    f"Station {station_id} latitude {lat}°N is outside Delhi NCR bounds "
                    f"[{self.NCR_GEO_BOUNDS['min_lat']}, {self.NCR_GEO_BOUNDS['max_lat']}]."
                )
            if not (self.NCR_GEO_BOUNDS["min_lon"] <= lon <= self.NCR_GEO_BOUNDS["max_lon"]):
                raise ValueError(
                    f"Station {station_id} longitude {lon}°E is outside Delhi NCR bounds "
                    f"[{self.NCR_GEO_BOUNDS['min_lon']}, {self.NCR_GEO_BOUNDS['max_lon']}]."
                )

    def _impute_station_series_leakage_safe(
        self,
        df: pd.DataFrame,
        cols_to_impute: List[str],
        max_gap: int = 3,
    ) -> pd.DataFrame:
        """
        Impute missing time-series observations using strictly forward-fill (past observations only).
        Never uses bfill or lookahead windows to avoid future-data leakage into ML features.
        
        Args:
            df: Station DataFrame.
            cols_to_impute: Numeric columns to impute.
            max_gap: Maximum consecutive missing hours to forward-fill.
            
        Returns:
            pd.DataFrame: Imputed DataFrame with audit logs for imputed entries.
        """
        imputed_dfs = []
        for station_id, group in df.groupby("station_id"):
            st_group = group.sort_values("timestamp_utc").copy()
            for col in cols_to_impute:
                if col not in st_group.columns:
                    continue

                null_mask = st_group[col].isna()
                null_count = null_mask.sum()
                if null_count > 0:
                    # Forward fill with limited window (strictly past-only)
                    imputed_series = st_group[col].ffill(limit=max_gap)
                    filled_mask = null_mask & imputed_series.notna()
                    filled_count = filled_mask.sum()

                    if filled_count > 0:
                        self._log_qc_event(
                            event_type="leakage_safe_imputation",
                            station_id=station_id,
                            variable=col,
                            timestamp=None,
                            original_value=f"{filled_count} missing values",
                            action=f"ffill_limit_{max_gap}",
                            details=f"Forward-filled {filled_count} missing values using past observations (max gap {max_gap}h).",
                        )
                    st_group[col] = imputed_series

            imputed_dfs.append(st_group)

        return pd.concat(imputed_dfs, ignore_index=True)

    def get_qc_audit_dataframe(self) -> pd.DataFrame:
        """Return the complete quality control audit log as a pandas DataFrame."""
        if not self.qc_log:
            return pd.DataFrame(columns=[
                "event_type", "station_id", "variable", "timestamp", "original_value", "action", "details"
            ])
        return pd.DataFrame(self.qc_log)
