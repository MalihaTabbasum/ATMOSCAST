"""
Open-Meteo Historical & Boundary-Layer Weather Collector
Fetches hourly surface meteorology and boundary-layer height for Delhi NCR monitoring stations.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import requests

from src.data_collection.base import BaseDataCollector, logger


class OpenMeteoCollector(BaseDataCollector):
    """Collector for Open-Meteo Historical Weather and Atmospheric Forecast APIs."""

    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    DEFAULT_HOURLY_VARS = [
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "surface_pressure",
        "wind_speed_10m",
        "wind_direction_10m",
        "precipitation",
        "boundary_layer_height",
    ]

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ):
        super().__init__(
            source_name="Open-Meteo",
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )

    def health_check(self) -> Dict[str, Any]:
        """Verify Open-Meteo API availability using Delhi coordinates."""
        try:
            resp = self.fetch_url(
                self.ARCHIVE_URL,
                params={
                    "latitude": 28.6469,
                    "longitude": 77.3160,
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-01",
                    "hourly": "temperature_2m",
                },
            )
            is_ok = resp.status_code == 200
            return {
                "source": self.source_name,
                "status": "connected" if is_ok else "degraded",
                "status_code": resp.status_code,
                "latency_ms": int(resp.elapsed.total_seconds() * 1000),
                "auth_required": False,
            }
        except Exception as e:
            return {
                "source": self.source_name,
                "status": "unreachable",
                "error": str(e),
                "auth_required": False,
            }

    def fetch_station_weather(
        self,
        station_id: str,
        station_name: str,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        hourly_variables: Optional[List[str]] = None,
        save_raw: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch historical hourly weather for a specific station coordinate.
        
        Args:
            station_id: Unique station identifier (e.g. 'delhi_anand_vihar').
            station_name: Human readable station name.
            latitude: Station latitude.
            longitude: Station longitude.
            start_date: YYYY-MM-DD.
            end_date: YYYY-MM-DD.
            hourly_variables: List of weather variables.
            save_raw: Whether to persist raw response to disk.
            
        Returns:
            Dict[str, Any]: Normalized weather dictionary containing hourly records and units.
        """
        if hourly_variables is None:
            hourly_variables = self.DEFAULT_HOURLY_VARS

        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ",".join(hourly_variables),
            "timezone": "UTC",
        }

        resp = self.fetch_url(self.ARCHIVE_URL, params=params)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Open-Meteo API returned error {resp.status_code}: {resp.text}"
            )

        data = resp.json()

        # Check for missing PBL height in archive; query forecast/reanalysis if available for recent dates
        hourly_data = data.get("hourly", {})
        pbl_values = hourly_data.get("boundary_layer_height", [])
        if pbl_values and all(v is None for v in pbl_values):
            logger.warning(
                f"[{self.source_name}] boundary_layer_height returned null for historical archive ({start_date} to {end_date}). "
                "Documenting in provenance."
            )

        provenance = {
            "station_id": station_id,
            "station_name": station_name,
            "latitude": latitude,
            "longitude": longitude,
            "requested_start_date": start_date,
            "requested_end_date": end_date,
            "api_endpoint": self.ARCHIVE_URL,
            "params": params,
            "hourly_units": data.get("hourly_units", {}),
            "elevation": data.get("elevation"),
        }

        if save_raw:
            filename = f"open_meteo_{station_id}_{start_date}_{end_date}.json"
            self.save_raw_payload(data, filename, provenance)

        return data

    @staticmethod
    def raw_to_dataframe(raw_payload: Dict[str, Any], station_id: str) -> pd.DataFrame:
        """
        Convert raw Open-Meteo payload into a standardized pandas DataFrame.
        
        Args:
            raw_payload: JSON payload returned by Open-Meteo API.
            station_id: Station identifier.
            
        Returns:
            pd.DataFrame: Hourly dataframe with parsed UTC timestamp index.
        """
        hourly = raw_payload.get("hourly", {})
        if not hourly or "time" not in hourly:
            return pd.DataFrame()

        df = pd.DataFrame(hourly)
        df["timestamp_utc"] = pd.to_datetime(df["time"], utc=True)
        df["station_id"] = station_id
        df["latitude"] = raw_payload.get("latitude")
        df["longitude"] = raw_payload.get("longitude")
        df.drop(columns=["time"], inplace=True)
        df.sort_values("timestamp_utc", inplace=True)
        df.drop_duplicates(subset=["station_id", "timestamp_utc"], inplace=True)
        return df
