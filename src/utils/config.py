"""
Configuration Loader Utility
Loads and validates settings from config/settings.yaml and environment variables.
"""

from pathlib import Path
import os
from typing import Any, Dict, List, Optional
import yaml


def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    # Since config.py is in src/utils/, parent.parent.parent is the project root
    return Path(__file__).resolve().parent.parent.parent


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load settings from YAML configuration file.
    
    Args:
        config_path: Optional explicit path to configuration YAML file.
                     Defaults to config/settings.yaml relative to project root.
                     
    Returns:
        Dict[str, Any]: Configuration dictionary.
        
    Raises:
        FileNotFoundError: If the configuration file is not found.
        yaml.YAMLError: If parsing fails.
    """
    if config_path is None:
        config_path = get_project_root() / "config" / "settings.yaml"

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found at: {config_path.resolve()}"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError(f"Invalid configuration format in {config_path}; expected a mapping.")

    # Override or inject environment variable sensitive fields if set
    _inject_env_overrides(config)

    return config


def _inject_env_overrides(config: Dict[str, Any]) -> None:
    """Safely apply environment variables to configuration without mutating defaults if absent."""
    if "api" not in config:
        config["api"] = {}

    openaq_key = os.getenv("OPENAQ_API_KEY")
    if openaq_key:
        config["api"]["openaq_api_key"] = openaq_key

    firms_key = os.getenv("NASA_FIRMS_MAP_KEY")
    if firms_key:
        config["api"]["nasa_firms_map_key"] = firms_key

    cpcb_key = os.getenv("CPCB_API_KEY")
    if cpcb_key:
        config["api"]["cpcb_api_key"] = cpcb_key


def get_stations(config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Retrieve the list of configured monitoring stations."""
    if config is None:
        config = load_config()
    return config.get("stations", [])


def get_pollutants(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Retrieve pollutant metadata and primary targets."""
    if config is None:
        config = load_config()
    return config.get("pollutants", {})


def get_forecast_horizons(config: Optional[Dict[str, Any]] = None) -> List[int]:
    """Retrieve supported forecast horizons in hours (e.g. [24, 48, 72])."""
    if config is None:
        config = load_config()
    return config.get("forecasting", {}).get("horizons_hours", [24, 48, 72])
