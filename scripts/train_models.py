"""
AtmosCast — Reproducible Model Training Script

Run this script to regenerate all 27 trained model artifacts from the
processed dataset. Required only if model .joblib files are absent.

Usage:
    python scripts/train_models.py

Prerequisites:
    pip install -r requirements.txt
    data/processed/merged_delhi_ncr_hourly.csv must exist
    (run preprocessing pipeline first if absent)

Output:
    models/*.joblib         (27 trained model artifacts)
    models/model_registry.json
    reports/model_comparison_report.md
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> None:
    from src.models.pipeline import MLPipeline

    data_path = _ROOT / "data" / "processed" / "merged_delhi_ncr_hourly.csv"
    models_dir = _ROOT / "models"
    reports_dir = _ROOT / "reports"

    if not data_path.exists():
        print(f"ERROR: Processed dataset not found at {data_path}")
        print("Run the preprocessing pipeline first:")
        print("  python -m src.preprocessing.pipeline")
        sys.exit(1)

    print("=" * 60)
    print("AtmosCast — Model Training Pipeline")
    print("=" * 60)
    print(f"Dataset  : {data_path}")
    print(f"Models   : {models_dir}")
    print(f"Reports  : {reports_dir}")
    print()

    pipeline = MLPipeline(
        data_path=str(data_path),
        models_dir=str(models_dir),
        reports_dir=str(reports_dir),
        target_pollutant="pm25",
        horizons=[24, 48, 72],
    )

    results = pipeline.run()

    print()
    print("=" * 60)
    print("Training complete.")
    print(f"Models serialized : {models_dir}")
    print(f"Registry          : {models_dir / 'model_registry.json'}")
    print(f"Report            : {reports_dir / 'model_comparison_report.md'}")
    print("=" * 60)
    return results


if __name__ == "__main__":
    main()
