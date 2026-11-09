"""
OpenAQ API v3 Collector
Implements location discovery, sensor mapping, and measurement retrieval
for Delhi NCR monitoring stations according to the official OpenAQ v3 specification.
"""

import os
from typing import Any, Dict, List, Optional
import pandas as pd

from src.data_collection.base import BaseDataCollector, logger
from src.utils.config import load_config


class OpenAQV3Collector(BaseDataCollector):
    """Client for OpenAQ API v3 (https://docs.openaq.org/)."""

    BASE_URL = "https://api.openaq.org/v3"

    # Standard OpenAQ pollutant parameter IDs / names
    TARGET_PARAMETERS = ["pm25", "pm10", "o3", "no2", "so2", "co"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 15,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ):
        super().__init__(
            source_name="OpenAQ-v3",
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )
        if api_key is None:
            config = load_config()
            api_key = os.getenv("OPENAQ_API_KEY") or config.get("api", {}).get("openaq_api_key")

        self.api_key = api_key

    def _get_headers(self) -> Dict[str, str]:
        """Construct request headers with OpenAQ v3 authentication."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "AtmosCast/1.0 (Delhi NCR Air Pollution Research)",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def health_check(self) -> Dict[str, Any]:
        """Verify API connectivity and authentication status."""
        url = f"{self.BASE_URL}/locations"
        params = {"limit": 1}
        headers = self._get_headers()

        if not self.api_key:
            return {
                "source": self.source_name,
                "status": "authentication_required",
                "message": (
                    "OpenAQ API v3 requires an API key in the 'X-API-Key' header. "
                    "Obtain a free key at https://openaq.org/ and set OPENAQ_API_KEY in your .env file."
                ),
                "auth_configured": False,
                "status_code": 401,
            }

        try:
            resp = self.fetch_url(url, params=params, headers=headers)
            if resp.status_code == 200:
                return {
                    "source": self.source_name,
                    "status": "connected",
                    "status_code": 200,
                    "auth_configured": True,
                    "latency_ms": int(resp.elapsed.total_seconds() * 1000),
                }
            elif resp.status_code == 401:
                return {
                    "source": self.source_name,
                    "status": "unauthorized",
                    "status_code": 401,
                    "message": "Invalid OPENAQ_API_KEY provided. Please check credentials in .env.",
                    "auth_configured": True,
                }
            else:
                return {
                    "source": self.source_name,
                    "status": "error",
                    "status_code": resp.status_code,
                    "message": resp.text[:200],
                    "auth_configured": True,
                }
        except Exception as e:
            return {
                "source": self.source_name,
                "status": "unreachable",
                "error": str(e),
                "auth_configured": bool(self.api_key),
            }

    def discover_delhi_locations(
        self,
        bbox: str = "76.8,28.2,77.6,28.9",
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """
        Discover monitoring stations within the Delhi NCR bounding box.
        
        Args:
            bbox: Bounding box string "minLon,minLat,maxLon,maxLat".
            limit: Maximum locations per page.
            
        Returns:
            List[Dict[str, Any]]: List of discovered locations with metadata and sensor ids.
        """
        if not self.api_key:
            raise PermissionError(
                "Cannot query OpenAQ API v3 without an API key. "
                "Please configure OPENAQ_API_KEY in .env."
            )

        url = f"{self.BASE_URL}/locations"
        params = {
            "bbox": bbox,
            "limit": limit,
        }
        headers = self._get_headers()

        resp = self.fetch_url(url, params=params, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(
                f"OpenAQ API v3 location discovery failed (HTTP {resp.status_code}): {resp.text}"
            )

        data = resp.json()
        results = data.get("results", [])
        logger.info(f"[{self.source_name}] Discovered {len(results)} locations in Delhi NCR bbox {bbox}.")
        return results

    def get_location_sensors(self, location_id: int) -> List[Dict[str, Any]]:
        """Retrieve all active measurement sensors for a specific location."""
        if not self.api_key:
            raise PermissionError("OPENAQ_API_KEY required to query sensors.")

        url = f"{self.BASE_URL}/locations/{location_id}/sensors"
        headers = self._get_headers()

        resp = self.fetch_url(url, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to fetch sensors for location {location_id} (HTTP {resp.status_code}): {resp.text}"
            )

        return resp.json().get("results", [])

    def collect_measurements(
        self,
        sensor_id: int,
        start_datetime: str,
        end_datetime: str,
        limit: int = 1000,
        save_raw: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Collect historical measurements for a specific sensor.
        
        Args:
            sensor_id: OpenAQ sensor ID.
            start_datetime: ISO8601 UTC string (e.g. '2024-01-01T00:00:00Z').
            end_datetime: ISO8601 UTC string (e.g. '2024-01-07T23:59:59Z').
            limit: Results per page.
            save_raw: Save raw payload with provenance.
            
        Returns:
            List[Dict[str, Any]]: Raw measurement records.
        """
        if not self.api_key:
            raise PermissionError("OPENAQ_API_KEY required to collect measurements.")

        url = f"{self.BASE_URL}/sensors/{sensor_id}/measurements"
        params = {
            "datetime_from": start_datetime,
            "datetime_to": end_datetime,
            "limit": limit,
        }
        headers = self._get_headers()

        all_records = []
        page = 1

        while True:
            params["page"] = page
            resp = self.fetch_url(url, params=params, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"OpenAQ measurement query failed on page {page} (HTTP {resp.status_code}): {resp.text}"
                )

            data = resp.json()
            records = data.get("results", [])
            if not records:
                break

            all_records.extend(records)
            meta = data.get("meta", {})
            total_pages = meta.get("totalPages", 1)
            if page >= total_pages or len(records) < limit:
                break
            page += 1

        if save_raw and all_records:
            filename = f"openaq_sensor_{sensor_id}_{start_datetime[:10]}_{end_datetime[:10]}.json"
            provenance = {
                "sensor_id": sensor_id,
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "record_count": len(all_records),
                "api_endpoint": url,
            }
            self.save_raw_payload({"results": all_records}, filename, provenance)

        return all_records

    @staticmethod
    def measurements_to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
        """Standardize OpenAQ measurement records into a structured DataFrame."""
        if not records:
            return pd.DataFrame()

        rows = []
        for r in records:
            period = r.get("period", {})
            datetime_to = period.get("datetimeTo", {})
            rows.append({
                "timestamp_utc": pd.to_datetime(datetime_to.get("utc"), utc=True),
                "value": r.get("value"),
                "parameter": r.get("parameter", {}).get("name"),
                "units": r.get("parameter", {}).get("units"),
            })

        df = pd.DataFrame(rows)
        df.dropna(subset=["timestamp_utc", "value"], inplace=True)
        df.drop_duplicates(subset=["timestamp_utc", "parameter"], inplace=True)
        df.sort_values("timestamp_utc", inplace=True)
        return df
