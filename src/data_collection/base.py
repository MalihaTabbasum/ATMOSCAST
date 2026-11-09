"""
Base Data Collector
Abstract base class providing robust HTTP session management, exponential backoff,
retries, timeout handling, raw dataset persistence, and provenance tracking.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils.config import get_project_root, load_config

logger = logging.getLogger("AtmosCast.DataCollection")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class BaseDataCollector(ABC):
    """Abstract base class for all AtmosCast data ingestion clients."""

    def __init__(
        self,
        source_name: str,
        timeout: int = 15,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ):
        self.source_name = source_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = self._create_resilient_session()
        self.project_root = get_project_root()
        self.raw_data_dir = self.project_root / "data" / "raw"
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    def _create_resilient_session(self) -> requests.Session:
        """Create a requests session with automatic retries and exponential backoff."""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def fetch_url(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """
        Execute an HTTP GET request with timeouts and standardized error logging.
        
        Args:
            url: Target API endpoint.
            params: Query parameters.
            headers: Request headers.
            
        Returns:
            requests.Response: Response object.
            
        Raises:
            requests.RequestException: If network fails or timeout is exceeded.
        """
        logger.info(f"[{self.source_name}] Querying: {url} with params {params}")
        try:
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
            return response
        except requests.Timeout as e:
            logger.error(f"[{self.source_name}] Request timed out after {self.timeout}s: {e}")
            raise
        except requests.RequestException as e:
            logger.error(f"[{self.source_name}] Request failed: {e}")
            raise

    def save_raw_payload(
        self,
        payload: Dict[str, Any],
        filename: str,
        provenance_meta: Dict[str, Any],
    ) -> Path:
        """
        Save raw JSON payload and an associated provenance sidecar file.
        
        Args:
            payload: Raw JSON data from API.
            filename: Target filename (e.g., 'open_meteo_anand_vihar_2024-01-01.json').
            provenance_meta: Provenance metadata (retrieval time, source URL, parameters, units).
            
        Returns:
            Path: Path to saved file.
        """
        file_path = self.raw_data_dir / filename
        prov_path = self.raw_data_dir / f"{file_path.stem}_provenance.json"

        # Record system timestamp
        provenance_meta["retrieved_at_utc"] = datetime.now(timezone.utc).isoformat()
        provenance_meta["collector"] = self.source_name
        provenance_meta["target_file"] = filename

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        with open(prov_path, "w", encoding="utf-8") as f:
            json.dump(provenance_meta, f, indent=2)

        logger.info(f"[{self.source_name}] Saved raw data to {file_path.name} with provenance sidecar.")
        return file_path

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform a quick endpoint connectivity and health audit."""
        pass
