"""
Deployment patch script: Update hardcoded relative paths in UI view modules
to use project-root-relative resolution compatible with Streamlit Cloud.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def patch_performance():
    fpath = PROJECT_ROOT / "src" / "ui" / "views" / "performance.py"
    content = fpath.read_text(encoding="utf-8")

    old_import_block = (
        "from src.evaluation.plots import plot_model_comparison_bars, plot_horizon_error_trajectory\n"
        "\n"
        "\n"
        "def render_performance_view():"
    )
    new_import_block = (
        "from src.evaluation.plots import plot_model_comparison_bars, plot_horizon_error_trajectory\n"
        "\n"
        "# Resolve project root relative to this file - works on Streamlit Cloud and locally\n"
        "_VIEW_DIR = Path(__file__).resolve().parent          # src/ui/views/\n"
        "_PROJECT_ROOT = _VIEW_DIR.parent.parent.parent       # project root\n"
        "\n"
        "\n"
        "def _find_path(relative: str) -> Path:\n"
        '    """Return first existing candidate: project-root/relative or cwd/relative."""\n'
        "    p1 = _PROJECT_ROOT / relative\n"
        "    p2 = Path(relative)\n"
        "    return p1 if p1.exists() else p2\n"
        "\n"
        "\n"
        "def render_performance_view():"
    )

    old_reg = '    reg_path = Path("models/model_registry.json")'
    new_reg = '    reg_path = _find_path("models/model_registry.json")'

    content = content.replace(old_import_block, new_import_block)
    content = content.replace(old_reg, new_reg)
    fpath.write_text(content, encoding="utf-8")
    print(f"Patched {fpath.name}")


def patch_explainability():
    fpath = PROJECT_ROOT / "src" / "ui" / "views" / "explainability.py"
    content = fpath.read_text(encoding="utf-8")

    old_cache_fn = (
        "@st.cache_resource\n"
        "def get_cached_explainer():\n"
        '    """Loads and caches the ModelExplainer for the 48h XGBoost Tier 2 model."""\n'
        '    artifact_path = Path("models/xgboost_tier2_pollution_and_weather_pm25_h48.joblib")\n'
        "    if not artifact_path.exists():\n"
        "        return None\n"
        "    return ModelExplainer(artifact_path)"
    )
    new_cache_fn = (
        "# Resolve project root relative to this file - works on Streamlit Cloud and locally\n"
        "_VIEW_DIR = Path(__file__).resolve().parent          # src/ui/views/\n"
        "_PROJECT_ROOT = _VIEW_DIR.parent.parent.parent       # project root\n"
        "\n"
        "\n"
        "def _find_artifact(relative: str) -> Path:\n"
        '    """Return first existing candidate: project-root/relative or cwd/relative."""\n'
        "    p1 = _PROJECT_ROOT / relative\n"
        "    p2 = Path(relative)\n"
        "    return p1 if p1.exists() else p2\n"
        "\n"
        "\n"
        "@st.cache_resource\n"
        "def get_cached_explainer():\n"
        '    """Loads and caches the ModelExplainer for the 48h XGBoost Tier 2 model."""\n'
        "    artifact_path = _find_artifact(\n"
        '        "models/xgboost_tier2_pollution_and_weather_pm25_h48.joblib"\n'
        "    )\n"
        "    if not artifact_path.exists():\n"
        "        return None\n"
        "    return ModelExplainer(artifact_path)"
    )

    content = content.replace(old_cache_fn, new_cache_fn)
    fpath.write_text(content, encoding="utf-8")
    print(f"Patched {fpath.name}")


def patch_forecast_engine():
    """ForecastEngine uses models_dir='models' default - make it resolve from __file__."""
    fpath = PROJECT_ROOT / "src" / "forecasting" / "engine.py"
    content = fpath.read_text(encoding="utf-8")

    old_init = (
        "    def __init__(\n"
        "        self,\n"
        '        models_dir: str = "models",\n'
        '        model_type: str = "xgboost",\n'
        '        tier_name: str = "tier2_pollution_and_weather",\n'
        '        target_pollutant: str = "pm25",\n'
        "        horizons: List[int] = [24, 48, 72],\n"
        "    ):\n"
        "        self.models_dir = Path(models_dir)\n"
    )
    new_init = (
        "    # Default models directory resolved from project root (robust for Streamlit Cloud)\n"
        "    _DEFAULT_MODELS_DIR = Path(__file__).resolve().parent.parent.parent / 'models'\n"
        "\n"
        "    def __init__(\n"
        "        self,\n"
        "        models_dir: str = \"\",\n"
        '        model_type: str = "xgboost",\n'
        '        tier_name: str = "tier2_pollution_and_weather",\n'
        '        target_pollutant: str = "pm25",\n'
        "        horizons: List[int] = [24, 48, 72],\n"
        "    ):\n"
        "        # Resolve models directory: explicit arg > project-root/models > cwd/models\n"
        "        if models_dir:\n"
        "            self.models_dir = Path(models_dir)\n"
        "        else:\n"
        "            self.models_dir = (\n"
        "                self._DEFAULT_MODELS_DIR\n"
        "                if self._DEFAULT_MODELS_DIR.exists()\n"
        "                else Path('models')\n"
        "            )\n"
    )

    content = content.replace(old_init, new_init)
    fpath.write_text(content, encoding="utf-8")
    print(f"Patched {fpath.name}")


if __name__ == "__main__":
    patch_performance()
    patch_explainability()
    patch_forecast_engine()
    print("All path patches applied successfully.")
