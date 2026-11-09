"""
Model Training Module for AtmosCast.

Orchestrates:
- Chronological train/validation/test splitting with zero future leakage
- Feature scaling fit strictly on training set
- Model fitting (Persistence baseline, Random Forest, XGBoost)
- Metric evaluation across horizons (24h, 48h, 72h) and feature tiers (A, B, C)
- Model artifact serialization with metadata
"""

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from src.models.baseline import PersistenceForecaster


def compute_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes standard atmospheric forecasting evaluation metrics:
    - MAE: Mean Absolute Error (µg/m³)
    - RMSE: Root Mean Squared Error (µg/m³)
    - R2: Coefficient of Determination
    - MAPE: Mean Absolute Percentage Error (%)
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))

    # Guard against division by near-zero for MAPE
    safe_true = np.where(np.abs(y_true) < 1.0, 1.0, y_true)
    mape = float(np.mean(np.abs((y_true - y_pred) / safe_true)) * 100.0)

    return {
        "MAE": round(mae, 3),
        "RMSE": round(rmse, 3),
        "R2": round(r2, 4),
        "MAPE": round(mape, 2),
    }


class ModelTrainer:
    """
    Trains and evaluates multi-horizon direct forecasting models across feature tiers.
    """

    SUPPORTED_MODELS = ["persistence", "random_forest", "xgboost"]
    HORIZONS = [24, 48, 72]

    def __init__(
        self,
        target_pollutant: str = "pm25",
        horizons: List[int] = [24, 48, 72],
        models_dir: str = "models",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_state: int = 42,
    ):
        self.target_pollutant = target_pollutant
        self.horizons = horizons
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.random_state = random_state

    def chronological_split(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        """
        Splits data chronologically per station to maintain temporal sequence
        and prevent lookahead leakage.
        """
        required_cols = feature_cols + [target_col, "station_id", "timestamp_utc"]
        clean_df = df[required_cols].dropna().copy()
        clean_df = clean_df.sort_values(by=["station_id", "timestamp_utc"]).reset_index(drop=True)

        train_indices = []
        val_indices = []
        test_indices = []

        for station_id, group in clean_df.groupby("station_id"):
            n = len(group)
            train_end = int(n * self.train_ratio)
            val_end = int(n * (self.train_ratio + self.val_ratio))

            station_idx = group.index.tolist()
            train_indices.extend(station_idx[:train_end])
            val_indices.extend(station_idx[train_end:val_end])
            test_indices.extend(station_idx[val_end:])

        train_df = clean_df.loc[train_indices]
        val_df = clean_df.loc[val_indices]
        test_df = clean_df.loc[test_indices]

        X_train = train_df[feature_cols]
        y_train = train_df[target_col]
        X_val = val_df[feature_cols]
        y_val = val_df[target_col]
        X_test = test_df[feature_cols]
        y_test = test_df[target_col]

        return X_train, X_val, X_test, y_train, y_val, y_test

    def get_model_instance(self, model_type: str, horizon: int) -> Any:
        """
        Instantiates the requested model with robust hyperparameters suited
        for atmospheric tabular time-series.
        """
        if model_type == "persistence":
            return PersistenceForecaster(
                target_column=self.target_pollutant,
                strategy="naive",
                horizon=horizon,
            )
        elif model_type == "random_forest":
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=8,
                min_samples_split=4,
                min_samples_leaf=2,
                random_state=self.random_state,
                n_jobs=-1,
            )
        elif model_type == "xgboost":
            return XGBRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=self.random_state,
                n_jobs=-1,
            )
        else:
            raise ValueError(f"Unsupported model type '{model_type}'. Choose from {self.SUPPORTED_MODELS}")

    def train_single_model(
        self,
        df: pd.DataFrame,
        model_type: str,
        tier_name: str,
        feature_cols: List[str],
        horizon: int,
    ) -> Dict[str, Any]:
        """
        Trains, evaluates, and serializes a single model configuration.
        """
        target_col = f"target_{self.target_pollutant}_h{horizon}"
        if target_col not in df.columns:
            raise KeyError(f"Target column '{target_col}' not found in DataFrame.")

        X_train, X_val, X_test, y_train, y_val, y_test = self.chronological_split(
            df=df,
            feature_cols=feature_cols,
            target_col=target_col,
        )

        # Fit feature scaler strictly on training features
        scaler = StandardScaler()
        scaler.fit(X_train)

        model = self.get_model_instance(model_type, horizon)

        # Train model
        model.fit(X_train, y_train)

        # Evaluate on Train, Val, Test
        train_preds = model.predict(X_train)
        val_preds = model.predict(X_val)
        test_preds = model.predict(X_test)

        train_metrics = compute_regression_metrics(y_train.to_numpy(), train_preds)
        val_metrics = compute_regression_metrics(y_val.to_numpy(), val_preds)
        test_metrics = compute_regression_metrics(y_test.to_numpy(), test_preds)

        artifact_name = f"{model_type}_{tier_name}_{self.target_pollutant}_h{horizon}.joblib"
        artifact_path = self.models_dir / artifact_name

        artifact_payload = {
            "model": model,
            "scaler": scaler,
            "model_type": model_type,
            "tier_name": tier_name,
            "target_pollutant": self.target_pollutant,
            "horizon": horizon,
            "feature_names": feature_cols,
            "train_sample_count": len(X_train),
            "val_sample_count": len(X_val),
            "test_sample_count": len(X_test),
            "train_metrics": train_metrics,
            "val_metrics": val_metrics,
            "test_metrics": test_metrics,
            "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        }

        joblib.dump(artifact_payload, artifact_path)

        return {
            "model_type": model_type,
            "tier_name": tier_name,
            "target_pollutant": self.target_pollutant,
            "horizon": horizon,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "train_metrics": train_metrics,
            "val_metrics": val_metrics,
            "test_metrics": test_metrics,
            "artifact_path": str(artifact_path),
        }

    def train_full_matrix(
        self,
        df: pd.DataFrame,
        feature_tiers: Dict[str, List[str]],
        model_types: Optional[List[str]] = None,
        horizons: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes grid of all model types, feature tiers, and forecast horizons.
        """
        model_types = model_types or self.SUPPORTED_MODELS
        horizons = horizons or self.horizons
        results: List[Dict[str, Any]] = []

        for h in horizons:
            for tier_name, features in feature_tiers.items():
                for m_type in model_types:
                    res = self.train_single_model(
                        df=df,
                        model_type=m_type,
                        tier_name=tier_name,
                        feature_cols=features,
                        horizon=h,
                    )
                    results.append(res)

        return results
