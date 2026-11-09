"""
UI Package for AtmosCast.
"""

from src.ui.theme import CUSTOM_CSS
from src.ui.views.overview import render_overview_view
from src.ui.views.air_quality import render_air_quality_view
from src.ui.views.forecast import render_forecast_view
from src.ui.views.weather import render_weather_view
from src.ui.views.episodes import render_episodes_view
from src.ui.views.performance import render_performance_view
from src.ui.views.explainability import render_explainability_view
from src.ui.views.about import render_about_view

__all__ = [
    "CUSTOM_CSS",
    "render_overview_view",
    "render_air_quality_view",
    "render_forecast_view",
    "render_weather_view",
    "render_episodes_view",
    "render_performance_view",
    "render_explainability_view",
    "render_about_view",
]
