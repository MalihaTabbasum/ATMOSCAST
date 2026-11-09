"""
SHAP Explainability and Attribution Engine for AtmosCast.

Wraps shap.TreeExplainer to compute:
- Global feature importance (mean absolute SHAP values)
- Feature group attributions (Pollution History vs. Weather vs. Stability vs. Temporal)
- Local individual prediction waterfall decompositions
- Meteorological sensitivity and non-linear threshold dependencies
"""

import os
from pathlib import Path
import tempfile
from typing import Any, Dict, List, Tuple, Union
import joblib
import numpy as np
import pandas as pd
import shap

# Ensure writable matplotlib cache dir in sandboxed environments
os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()


class ModelExplainer:
    """
    Computes and aggregates SHAP explainability values for AtmosCast tree-based models.
    """

    FEATURE_GROUPS = {
        "Pollution History": [
            "pm25", "pm10", "no2", "o3",
            "pm25_lag_", "pm10_lag_", "no2_lag_", "o3_lag_",
            "pm25_roll_", "pm10_roll_",
        ],
        "Surface Meteorology": [
            "temperature_2m", "relative_humidity_2m", "dew_point_2m",
            "surface_pressure", "wind_speed_10m", "precipitation",
            "wind_dir_sin", "wind_dir_cos",
            "temperature_2m_lag_", "wind_speed_10m_lag_", "relative_humidity_2m_lag_",
            "wind_speed_10m_roll_", "temperature_2m_roll_",
        ],
        "Atmospheric Stability & Inversion Proxies": [
            "dew_point_depression", "stagnation_index", "inversion_risk_index",
            "wind_humidity_ratio", "temp_rh_interaction", "pressure_tendency_3h",
        ],
        "Temporal & Diurnal Cycles": [
            "hour_sin", "hour_cos", "day_of_week_sin", "day_of_week_cos",
            "is_weekend", "month_sin", "month_cos", "is_winter",
        ],
    }

    def __init__(self, model_artifact: Union[str, Path, Dict[str, Any]]):
        if isinstance(model_artifact, (str, Path)):
            path = Path(model_artifact)
            if not path.exists():
                raise FileNotFoundError(f"Artifact not found: {path}")
            self.artifact = joblib.load(path)
        else:
            self.artifact = model_artifact

        self.model = self.artifact["model"]
        self.feature_names: List[str] = self.artifact["feature_names"]
        self.target_pollutant: str = self.artifact.get("target_pollutant", "pm25")
        self.horizon: int = self.artifact.get("horizon", 24)
        self.tier_name: str = self.artifact.get("tier_name", "unknown")
        self.model_type: str = self.artifact.get("model_type", "unknown")

        # Initialize TreeExplainer
        self.explainer = shap.TreeExplainer(self.model)

    def compute_shap_values(self, X: pd.DataFrame) -> Tuple[np.ndarray, float]:
        """
        Computes SHAP values matrix and base value E[f(X)].
        """
        aligned_X = X[self.feature_names]
        shap_values = self.explainer.shap_values(aligned_X)

        base_val = self.explainer.expected_value
        if isinstance(base_val, np.ndarray):
            base_val = float(base_val[0])
        else:
            base_val = float(base_val)

        return shap_values, base_val

    def get_global_importance(self, X: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
        """
        Computes mean absolute SHAP value for each feature, ranked in descending order.
        """
        shap_values, _ = self.compute_shap_values(X)
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

        df_importance = pd.DataFrame({
            "feature": self.feature_names,
            "mean_abs_shap": mean_abs_shap,
        }).sort_values(by="mean_abs_shap", ascending=False).reset_index(drop=True)

        # Categorize features into functional groups
        df_importance["group"] = df_importance["feature"].apply(self._categorize_feature)

        return df_importance.head(top_n)

    def get_group_contributions(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates SHAP feature importance into macro groups:
        Pollution History, Surface Meteorology, Atmospheric Stability, and Temporal Cycles.
        """
        shap_values, _ = self.compute_shap_values(X)
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

        group_sums: Dict[str, float] = {k: 0.0 for k in self.FEATURE_GROUPS.keys()}
        group_sums["Other / Unclassified"] = 0.0

        for feat, val in zip(self.feature_names, mean_abs_shap):
            grp = self._categorize_feature(feat)
            group_sums[grp] += float(val)

        total = sum(group_sums.values()) if sum(group_sums.values()) > 0 else 1.0

        records = [
            {
                "group": grp,
                "importance": round(val, 3),
                "percentage": round((val / total) * 100.0, 1),
            }
            for grp, val in group_sums.items()
            if val > 0
        ]
        return pd.DataFrame(records).sort_values(by="importance", ascending=False).reset_index(drop=True)

    def explain_single_prediction(
        self,
        X_row: pd.Series,
        top_n: int = 8,
    ) -> Dict[str, Any]:
        """
        Decomposes an individual prediction into baseline + feature contributions.
        """
        df_row = pd.DataFrame([X_row])[self.feature_names]
        shap_values, base_val = self.compute_shap_values(df_row)
        shap_row = shap_values[0]

        pred_val = float(self.model.predict(df_row)[0])

        # Rank features by absolute impact for this specific row
        feat_df = pd.DataFrame({
            "feature": self.feature_names,
            "value": df_row.iloc[0].values,
            "shap_value": shap_row,
            "abs_shap": np.abs(shap_row),
            "group": [self._categorize_feature(f) for f in self.feature_names],
        }).sort_values(by="abs_shap", ascending=False).reset_index(drop=True)

        top_features = feat_df.head(top_n).to_dict(orient="records")

        return {
            "base_value": round(base_val, 2),
            "prediction": round(pred_val, 2),
            "target_pollutant": self.target_pollutant,
            "horizon": self.horizon,
            "top_contributions": top_features,
            "full_shap_df": feat_df,
        }

    def _categorize_feature(self, feature_name: str) -> str:
        for grp, prefixes in self.FEATURE_GROUPS.items():
            for p in prefixes:
                if feature_name.startswith(p) or feature_name == p:
                    return grp
        return "Other / Unclassified"
