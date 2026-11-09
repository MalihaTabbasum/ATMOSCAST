"""
Feature Engineering Module for AtmosCast.

Constructs multi-tier feature representations coupling:
- Pollution history and lagged observations
- Multi-scale rolling statistical aggregations (leakage-free)
- Cyclical temporal encodings (diurnal, weekly, seasonal)
- Circular trigonometric wind representations
- Surface boundary-layer meteorology
- Atmospheric stability, nocturnal inversion indicators, and stagnation proxies

All transformations enforce strict chronological isolation with zero future-lookahead leakage.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


class FeatureEngineer:
    """
    Orchestrates time-series feature engineering and multi-horizon target generation
    across Delhi NCR monitoring stations.
    """

    POLLUTANTS = ["pm25", "pm10", "no2", "o3"]
    PRIMARY_TARGET = "pm25"
    HORIZONS = [24, 48, 72]

    TIER1_POLLUTION_ONLY = "tier1_pollution_only"
    TIER2_POLLUTION_WEATHER = "tier2_pollution_and_weather"
    TIER3_COUPLED_ATMOSPHERIC = "tier3_coupled_atmospheric"

    def __init__(self, target_pollutant: str = "pm25"):
        self.target_pollutant = target_pollutant
        self.feature_columns_by_tier: Dict[str, List[str]] = {}

    def extract_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts cyclical trigonometric temporal encodings from timestamp_ist.
        """
        df = df.copy()
        if "timestamp_ist" not in df.columns:
            if "timestamp_utc" in df.columns:
                df["timestamp_ist"] = pd.to_datetime(df["timestamp_utc"]).dt.tz_convert("Asia/Kolkata")
            else:
                raise KeyError("DataFrame must contain timestamp_ist or timestamp_utc.")

        ts = pd.to_datetime(df["timestamp_ist"])
        hour = ts.dt.hour
        day_of_week = ts.dt.dayofweek
        month = ts.dt.month

        # Cyclical diurnal (24 hours)
        df["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
        df["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)

        # Cyclical weekly (7 days)
        df["day_of_week_sin"] = np.sin(2 * np.pi * day_of_week / 7.0)
        df["day_of_week_cos"] = np.cos(2 * np.pi * day_of_week / 7.0)
        df["is_weekend"] = day_of_week.isin([5, 6]).astype(float)

        # Cyclical annual (12 months)
        df["month_sin"] = np.sin(2 * np.pi * month / 12.0)
        df["month_cos"] = np.cos(2 * np.pi * month / 12.0)
        df["is_winter"] = month.isin([11, 12, 1, 2]).astype(float)

        return df

    def extract_circular_wind(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Decomposes meteorological wind direction (0-360 deg) into orthogonal
        continuous sin/cos components to preserve circular continuity across 360/0 deg.
        """
        df = df.copy()
        if "wind_direction_10m" in df.columns:
            rad = np.radians(df["wind_direction_10m"].fillna(0.0))
            df["wind_dir_sin"] = np.sin(rad)
            df["wind_dir_cos"] = np.cos(rad)
        return df

    def compute_station_lags_and_rolling(
        self,
        df: pd.DataFrame,
        pollutant_lags: List[int] = [1, 2, 3, 6, 12, 24],
        weather_lags: List[int] = [1, 2, 3, 6, 12],
        rolling_windows: List[int] = [6, 12, 24],
    ) -> pd.DataFrame:
        """
        Generates lag and rolling statistics grouped strictly by station_id to prevent
        cross-station leakage. Rolling statistics only consume historical observations (closed='left').
        """
        df = df.copy()
        df = df.sort_values(by=["station_id", "timestamp_utc"]).reset_index(drop=True)

        grouped = df.groupby("station_id")

        # 1. Pollution Lags
        for poll in ["pm25", "pm10", "no2", "o3"]:
            if poll in df.columns:
                for lag in pollutant_lags:
                    df[f"{poll}_lag_{lag}"] = grouped[poll].shift(lag)

        # 2. Weather Lags
        weather_cols = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "surface_pressure"]
        for w_col in weather_cols:
            if w_col in df.columns:
                for lag in weather_lags:
                    df[f"{w_col}_lag_{lag}"] = grouped[w_col].shift(lag)

        # 3. Rolling window statistics on historical observations
        # Using shift(1) before rolling ensures zero leakage of the current time step's target
        for poll in ["pm25", "pm10"]:
            if poll in df.columns:
                shifted = grouped[poll].shift(1)
                for w in rolling_windows:
                    df[f"{poll}_roll_mean_{w}h"] = shifted.groupby(df["station_id"]).transform(
                        lambda s: s.rolling(w, min_periods=max(1, w // 2)).mean()
                    )
                    df[f"{poll}_roll_std_{w}h"] = shifted.groupby(df["station_id"]).transform(
                        lambda s: s.rolling(w, min_periods=max(1, w // 2)).std()
                    ).fillna(0.0)
                    df[f"{poll}_roll_max_{w}h"] = shifted.groupby(df["station_id"]).transform(
                        lambda s: s.rolling(w, min_periods=max(1, w // 2)).max()
                    )
                    df[f"{poll}_roll_min_{w}h"] = shifted.groupby(df["station_id"]).transform(
                        lambda s: s.rolling(w, min_periods=max(1, w // 2)).min()
                    )

        # Rolling weather aggregates
        if "wind_speed_10m" in df.columns:
            w_shifted = grouped["wind_speed_10m"].shift(1)
            df["wind_speed_10m_roll_mean_6h"] = w_shifted.groupby(df["station_id"]).transform(
                lambda s: s.rolling(6, min_periods=3).mean()
            )
            df["wind_speed_10m_roll_min_6h"] = w_shifted.groupby(df["station_id"]).transform(
                lambda s: s.rolling(6, min_periods=3).min()
            )

        if "temperature_2m" in df.columns:
            t_shifted = grouped["temperature_2m"].shift(1)
            df["temperature_2m_roll_mean_24h"] = t_shifted.groupby(df["station_id"]).transform(
                lambda s: s.rolling(24, min_periods=12).mean()
            )

        return df

    def compute_atmospheric_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Constructs micrometeorological proxies for boundary layer compression,
        temperature inversions, and atmospheric stagnation.
        """
        df = df.copy()

        # Dew point depression: T - Td (measures saturation deficit; close to 0 indicates fog/smog saturation)
        if "temperature_2m" in df.columns and "dew_point_2m" in df.columns:
            df["dew_point_depression"] = df["temperature_2m"] - df["dew_point_2m"]

        # Stagnation Index: Calm surface winds (< 5 km/h) combined with high humidity (> 80%)
        if "wind_speed_10m" in df.columns and "relative_humidity_2m" in df.columns:
            df["stagnation_index"] = (
                (df["wind_speed_10m"] < 5.0) & (df["relative_humidity_2m"] > 80.0)
            ).astype(float)
            df["wind_humidity_ratio"] = df["relative_humidity_2m"] / (df["wind_speed_10m"] + 1.0)
            df["temp_rh_interaction"] = (df["temperature_2m"] * df["relative_humidity_2m"]) / 100.0

        # Nocturnal Inversion Proxy: Nighttime (22:00 to 07:00 IST) with cold surface air (< 8 C) and calm wind
        if "timestamp_ist" in df.columns and "temperature_2m" in df.columns and "wind_speed_10m" in df.columns:
            hour = pd.to_datetime(df["timestamp_ist"]).dt.hour
            is_night = hour.isin([22, 23, 0, 1, 2, 3, 4, 5, 6, 7])
            df["inversion_risk_index"] = (
                is_night & (df["temperature_2m"] < 8.0) & (df["wind_speed_10m"] < 5.0)
            ).astype(float)

        # 3-Hour Surface Pressure Tendency (barometric subsidence marker)
        if "surface_pressure" in df.columns and "surface_pressure_lag_3" in df.columns:
            df["pressure_tendency_3h"] = df["surface_pressure"] - df["surface_pressure_lag_3"]

        return df

    def create_multi_horizon_targets(
        self,
        df: pd.DataFrame,
        horizons: List[int] = [24, 48, 72],
        pollutant: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Generates direct forward target columns shifted by -h hours per station.
        """
        df = df.copy()
        pollutant = pollutant or self.target_pollutant
        grouped = df.groupby("station_id")

        for h in horizons:
            col_name = f"target_{pollutant}_h{h}"
            df[col_name] = grouped[pollutant].shift(-h)

        return df

    def build_feature_tiers(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Defines the canonical list of feature columns for each model ablation tier.
        """
        all_cols = set(df.columns)

        # Tier 1: Pollution History Only
        tier1_candidates = [
            # Current values
            "pm25", "pm10", "no2", "o3",
            # Lags
            "pm25_lag_1", "pm25_lag_2", "pm25_lag_3", "pm25_lag_6", "pm25_lag_12", "pm25_lag_24",
            "pm10_lag_1", "pm10_lag_2", "pm10_lag_3", "pm10_lag_6", "pm10_lag_12", "pm10_lag_24",
            "no2_lag_1", "o3_lag_1",
            # Rolling statistics
            "pm25_roll_mean_6h", "pm25_roll_std_6h", "pm25_roll_max_6h", "pm25_roll_min_6h",
            "pm25_roll_mean_12h", "pm25_roll_std_12h",
            "pm25_roll_mean_24h", "pm25_roll_std_24h", "pm25_roll_max_24h", "pm25_roll_min_24h",
            "pm10_roll_mean_6h", "pm10_roll_mean_24h",
            # Temporal Cyclical
            "hour_sin", "hour_cos", "day_of_week_sin", "day_of_week_cos", "is_weekend",
            "month_sin", "month_cos", "is_winter",
        ]
        tier1_features = [c for c in tier1_candidates if c in all_cols]

        # Tier 2: Pollution + Direct Surface Weather
        tier2_candidates = tier1_features + [
            # Direct Weather
            "temperature_2m", "relative_humidity_2m", "dew_point_2m", "surface_pressure",
            "wind_speed_10m", "precipitation",
            # Circular Wind
            "wind_dir_sin", "wind_dir_cos",
            # Weather Lags
            "temperature_2m_lag_1", "temperature_2m_lag_2", "temperature_2m_lag_6",
            "relative_humidity_2m_lag_1", "relative_humidity_2m_lag_6",
            "wind_speed_10m_lag_1", "wind_speed_10m_lag_2", "wind_speed_10m_lag_6",
            "surface_pressure_lag_1", "surface_pressure_lag_6",
            # Weather Rolling
            "wind_speed_10m_roll_mean_6h", "wind_speed_10m_roll_min_6h",
            "temperature_2m_roll_mean_24h",
        ]
        tier2_features = [c for c in tier2_candidates if c in all_cols]

        # Tier 3: Extended Atmospheric Coupling
        tier3_candidates = tier2_features + [
            "dew_point_depression",
            "stagnation_index",
            "wind_humidity_ratio",
            "temp_rh_interaction",
            "inversion_risk_index",
            "pressure_tendency_3h",
        ]
        tier3_features = [c for c in tier3_candidates if c in all_cols]

        self.feature_columns_by_tier = {
            self.TIER1_POLLUTION_ONLY: tier1_features,
            self.TIER2_POLLUTION_WEATHER: tier2_features,
            self.TIER3_COUPLED_ATMOSPHERIC: tier3_features,
        }
        return self.feature_columns_by_tier

    def process_dataset(
        self,
        raw_df: pd.DataFrame,
        horizons: List[int] = [24, 48, 72],
        pollutant: str = "pm25",
    ) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
        """
        Executes the complete feature engineering pipeline on a coupled dataset.
        Returns the engineered DataFrame and the feature dictionary across all 3 tiers.
        """
        df = self.extract_temporal_features(raw_df)
        df = self.extract_circular_wind(df)
        df = self.compute_station_lags_and_rolling(df)
        df = self.compute_atmospheric_indicators(df)
        df = self.create_multi_horizon_targets(df, horizons=horizons, pollutant=pollutant)
        tiers = self.build_feature_tiers(df)
        return df, tiers
