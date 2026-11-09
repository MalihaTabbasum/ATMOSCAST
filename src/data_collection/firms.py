"""
NASA FIRMS (Fire Information for Resource Management System) Collector
Fetches satellite active fire detections and Fire Radiative Power (FRP) metrics
for the upwind agricultural stubble burning corridor (Punjab & Haryana).
Implemented as an optional data source.
"""

import os
from typing import Any, Dict, Optional
import io
import pandas as pd

from src.data_collection.base import BaseDataCollector, logger
from src.utils.config import load_config


class FIRMSCollector(BaseDataCollector):
    """Client for NASA FIRMS satellite active fire data."""

    BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

    # Default bounding box for Punjab & Haryana upwind corridor
    DEFAULT_AREA = "74.0,29.5,77.0,32.5"  # minLon, minLat, maxLon, maxLat
    DEFAULT_SOURCE = "VIIRS_SNPP_NRT"

    def __init__(
        self,
        map_key: Optional[str] = None,
        timeout: int = 15,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ):
        super().__init__(
            source_name="NASA-FIRMS",
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )
        if map_key is None:
            config = load_config()
            map_key = os.getenv("NASA_FIRMS_MAP_KEY") or config.get("api", {}).get("nasa_firms_map_key")

        self.map_key = map_key

    def health_check(self) -> Dict[str, Any]:
        """Check status of NASA FIRMS integration."""
        if not self.map_key:
            return {
                "source": self.source_name,
                "status": "optional_unconfigured",
                "message": (
                    "NASA FIRMS MAP_KEY is not set. Satellite fire tracking is optional. "
                    "To enable, request a free key at https://firms.modaps.eosdis.nasa.gov/api/map_key/ "
                    "and set NASA_FIRMS_MAP_KEY in your .env file."
                ),
                "auth_configured": False,
                "is_optional": True,
            }

        url = f"{self.BASE_URL}/{self.map_key}/{self.DEFAULT_SOURCE}/{self.DEFAULT_AREA}/1"
        try:
            resp = self.fetch_url(url)
            if resp.status_code == 200 and not resp.text.startswith("Invalid"):
                return {
                    "source": self.source_name,
                    "status": "connected",
                    "status_code": 200,
                    "auth_configured": True,
                    "is_optional": True,
                }
            else:
                return {
                    "source": self.source_name,
                    "status": "invalid_key",
                    "message": resp.text.strip(),
                    "auth_configured": True,
                    "is_optional": True,
                }
        except Exception as e:
            return {
                "source": self.source_name,
                "status": "unreachable",
                "error": str(e),
                "is_optional": True,
            }

    def fetch_active_fires(
        self,
        date_str: str,
        day_range: int = 1,
        area: Optional[str] = None,
        source: Optional[str] = None,
        save_raw: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch active fire detections for a given date and geographic bounding box.
        
        Args:
            date_str: YYYY-MM-DD format.
            day_range: Number of days (1 to 10).
            area: Bounding box "minLon,minLat,maxLon,maxLat".
            source: Satellite product (e.g. 'VIIRS_SNPP_NRT', 'MODIS_NRT').
            save_raw: Whether to persist CSV and provenance to disk.
            
        Returns:
            pd.DataFrame: Active fire detections DataFrame.
        """
        if not self.map_key:
            logger.warning(
                f"[{self.source_name}] MAP_KEY not configured. Skipping satellite fire fetch."
            )
            return pd.DataFrame()

        area = area or self.DEFAULT_AREA
        source = source or self.DEFAULT_SOURCE
        day_range = min(max(day_range, 1), 10)

        url = f"{self.BASE_URL}/{self.map_key}/{source}/{area}/{day_range}/{date_str}"
        resp = self.fetch_url(url)

        if resp.status_code != 200 or resp.text.startswith("Invalid"):
            raise RuntimeError(f"NASA FIRMS API error: {resp.text.strip()}")

        # Parse CSV response
        df = pd.read_csv(io.StringIO(resp.text))
        if df.empty:
            logger.info(f"[{self.source_name}] Zero fire detections returned for date {date_str}.")
            return df

        if save_raw:
            filename = f"firms_fires_{source}_{date_str}_range{day_range}.csv"
            raw_path = self.raw_data_dir / filename
            df.to_csv(raw_path, index=False)
            
            provenance = {
                "satellite_source": source,
                "area_bounding_box": area,
                "date": date_str,
                "day_range": day_range,
                "detection_count": len(df),
                "api_endpoint": f"{self.BASE_URL}/[KEY]/{source}/{area}/{day_range}/{date_str}",
            }
            prov_path = self.raw_data_dir / f"{raw_path.stem}_provenance.json"
            with open(prov_path, "w", encoding="utf-8") as f:
                import json
                json.dump(provenance, f, indent=2)

        return df
