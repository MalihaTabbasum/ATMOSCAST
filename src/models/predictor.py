"""
Model Prediction & Inference Module for AtmosCast.

Provides reusable prediction routines:
- Validates input features against model requirements
- Handles column alignment and schema integrity
- Generates point forecasts for 24h, 48h, and 72h horizons
"""

from pathlib import Path
from typing import Any, Dict, List, Union
import joblib
import numpy as np
import pandas as pd


class ModelPredictor:
    """
    Loads serialized AtmosCast model artifacts and executes inference with strict schema verification.
    """

    def __init__(self, artifact: Union[str, Path, Dict[str, Any]]):
        if isinstance(artifact, (str, Path)):
            path = Path(artifact)
            if not path.exists():
                raise FileNotFoundError(f"Model artifact not found at: {path}")
            self.artifact = joblib.load(path)
        elif isinstance(artifact, dict):
            self.artifact = artifact
        else:
            raise TypeError("Artifact must be a filepath (str/Path) or an artifact dictionary.")

        self._validate_artifact()
        self.model = self.artifact["model"]
        self.scaler = self.artifact.get("scaler")
        self.feature_names: List[str] = self.artifact["feature_names"]
        self.horizon: int = self.artifact.get("horizon", 24)
        self.target_pollutant: str = self.artifact.get("target_pollutant", "pm25")
        self.model_type: str = self.artifact.get("model_type", "unknown")
        self.tier_name: str = self.artifact.get("tier_name", "unknown")

    def _validate_artifact(self) -> None:
        required_keys = ["model", "feature_names"]
        for k in required_keys:
            if k not in self.artifact:
                raise KeyError(f"Corrupt artifact missing required key: '{k}'")

    def validate_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Ensures all expected feature columns are present and orders them consistently.
        """
        missing = [f for f in self.feature_names if f not in X.columns]
        if missing:
            raise ValueError(
                f"Input DataFrame is missing {len(missing)} required features for "
                f"{self.model_type} ({self.tier_name}): {missing[:5]}"
            )
        return X[self.feature_names]

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generates predictions from an input DataFrame.
        """
        aligned_X = self.validate_features(X)
        return self.model.predict(aligned_X)


class MultiHorizonPredictor:
    """
    Bundles trained models across 24h, 48h, and 72h horizons to generate
    simultaneous multi-horizon forecasts.
    """

    def __init__(
        self,
        models_dir: Union[str, Path] = "models",
        model_type: str = "xgboost",
        tier_name: str = "tier3_coupled_atmospheric",
        target_pollutant: str = "pm25",
        horizons: List[int] = [24, 48, 72],
    ):
        self.models_dir = Path(models_dir)
        self.model_type = model_type
        self.tier_name = tier_name
        self.target_pollutant = target_pollutant
        self.horizons = horizons
        self.predictors: Dict[int, ModelPredictor] = {}

        self._load_predictors()

    def _load_predictors(self) -> None:
        for h in self.horizons:
            artifact_name = f"{self.model_type}_{self.tier_name}_{self.target_pollutant}_h{h}.joblib"
            artifact_path = self.models_dir / artifact_name
            if artifact_path.exists():
                self.predictors[h] = ModelPredictor(artifact_path)
            else:
                raise FileNotFoundError(f"Required horizon artifact missing: {artifact_path}")

    def predict_all_horizons(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Returns a DataFrame containing predictions for all configured horizons.
        """
        results = {}
        for h, predictor in self.predictors.items():
            results[f"pred_{self.target_pollutant}_h{h}"] = predictor.predict(X)
        return pd.DataFrame(results, index=X.index)
