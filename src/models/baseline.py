"""
Baseline Forecasting Models for AtmosCast.

Implements benchmark persistence strategies:
1. Naive Persistence: y(t+h) = y(t)
2. Diurnal Rolling Persistence: y(t+h) = mean(y(t-23...t))
"""

from typing import Optional, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin


class PersistenceForecaster(BaseEstimator, RegressorMixin):
    """
    Persistence baseline forecaster for air quality time-series.
    Predicts future concentrations using current observations or rolling historical diurnal means.
    """

    def __init__(
        self,
        target_column: str = "pm25",
        strategy: str = "naive",  # 'naive' or 'diurnal_mean'
        horizon: int = 24,
    ):
        self.target_column = target_column
        self.strategy = strategy
        self.horizon = horizon
        self.fallback_value_: float = 0.0

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[Union[pd.Series, np.ndarray]] = None):
        """
        Fit records the historical mean from training data as a robust fallback for missing features.
        """
        if isinstance(X, pd.DataFrame):
            if self.target_column in X.columns:
                self.fallback_value_ = float(X[self.target_column].mean())
            elif y is not None:
                self.fallback_value_ = float(np.mean(y))
        elif y is not None:
            self.fallback_value_ = float(np.mean(y))
        return self

    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """
        Predicts future values based on the configured persistence strategy.
        """
        if isinstance(X, pd.DataFrame):
            if self.target_column in X.columns:
                preds = X[self.target_column].copy()
                if self.strategy == "diurnal_mean":
                    roll_col = f"{self.target_column}_roll_mean_24h"
                    if roll_col in X.columns:
                        preds = X[roll_col].copy()
                return preds.fillna(self.fallback_value_).to_numpy(dtype=float)

            # If target column is not present in X, use the first column or fallback
            if X.shape[1] > 0:
                return X.iloc[:, 0].fillna(self.fallback_value_).to_numpy(dtype=float)

        if isinstance(X, np.ndarray):
            if X.ndim == 2 and X.shape[1] > 0:
                return X[:, 0].astype(float)
            elif X.ndim == 1:
                return X.astype(float)

        return np.full(len(X), self.fallback_value_, dtype=float)
