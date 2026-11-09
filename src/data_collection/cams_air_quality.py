"""
Copernicus CAMS / Open-Meteo Atmospheric Air Quality Collector
Collects hourly historical concentrations of PM2.5, PM10, NO2, O3, SO2, and CO
for Delhi NCR monitoring stations from the Copernicus Atmosphere Monitoring Service reanalysis.
Provides authentic atmospheric data accessible without API key barriers.
"""

from typing import Any, Dict, List, Optional
import pandas as pd

from src.data_collection.base import BaseDataCollector


class CAMSAirQualityCollector(BaseDataCollector):
    """Client for Copernicus CAMS atmospheric chemical reanalysis data via Open-Meteo Air Quality API."""

    AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

    DEFAULT_POLLUTANTS = [
        "pm2_5",
        "pm10",
        "nitrogen_dioxide",
        "ozone",
        "sulphur_dioxide",
        "carbon_monoxide",
    ]

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ):
        super().__init__(
            source_name="Copernicus-CAMS",
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )

    def health_check(self) -> Dict[str, Any]:
        """Check API availability and response latency."""
        try:
            resp = self.fetch_url(
                self.AIR_QUALITY_URL,
                params={
                    "latitude": 28.6469,
                    "longitude": 77.3160,
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-01",
                    "hourly": "pm2_5,pm10",
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

    def fetch_station_air_quality(
        self,
        station_id: str,
        station_name: str,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        pollutants: Optional[List[str]] = None,
        save_raw: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch historical hourly pollutant concentrations for a station coordinate.
        
        Args:
            station_id: Station identifier.
            station_name: Station name.
            latitude: Latitude.
            longitude: Longitude.
            start_date: YYYY-MM-DD.
            end_date: YYYY-MM-DD.
            pollutants: List of pollutant variables.
            save_raw: Save raw JSON with provenance.
            
        Returns:
            Dict[str, Any]: Raw JSON response.
        """
        if pollutants is None:
            pollutants = self.DEFAULT_POLLUTANTS

        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ",".join(pollutants),
            "timezone": "UTC",
        }

        resp = self.fetch_url(self.AIR_QUALITY_URL, params=params)
        if resp.status_code != 200:
            raise RuntimeError(
                f"CAMS Air Quality API error (HTTP {resp.status_code}): {resp.text}"
            )

        data = resp.json()

        provenance = {
            "station_id": station_id,
            "station_name": station_name,
            "latitude": latitude,
            "longitude": longitude,
            "requested_start_date": start_date,
            "requested_end_date": end_date,
            "api_endpoint": self.AIR_QUALITY_URL,
            "params": params,
            "hourly_units": data.get("hourly_units", {}),
            "elevation": data.get("elevation"),
        }

        if save_raw:
            filename = f"cams_air_quality_{station_id}_{start_date}_{end_date}.json"
            self.save_raw_payload(data, filename, provenance)

        return data

    @staticmethod
    def raw_to_dataframe(raw_payload: Dict[str, Any], station_id: str) -> pd.DataFrame:
        """Standardize raw CAMS payload into a pandas DataFrame."""
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
