"""
Data Collection Package
Multi-source ingestion clients for Open-Meteo, OpenAQ v3, Copernicus CAMS, and NASA FIRMS.
"""

from src.data_collection.base import BaseDataCollector
from src.data_collection.open_meteo import OpenMeteoCollector
from src.data_collection.openaq import OpenAQV3Collector
from src.data_collection.cams_air_quality import CAMSAirQualityCollector
from src.data_collection.firms import FIRMSCollector
from src.data_collection.pipeline import DataCollectionPipeline

__all__ = [
    "BaseDataCollector",
    "OpenMeteoCollector",
    "OpenAQV3Collector",
    "CAMSAirQualityCollector",
    "FIRMSCollector",
    "DataCollectionPipeline",
]
