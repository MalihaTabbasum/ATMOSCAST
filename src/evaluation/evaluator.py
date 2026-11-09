"""
Model Evaluation and Diagnostic Module for AtmosCast.

Performs:
- Chronological validation and test set evaluations
- Validation-driven model selection without test-set leakage
- Horizon-wise error breakdown (24h, 48h, 72h)
- High-pollution severe episode diagnostics and systematic bias (MBE) analysis
- Atmospheric regime stratification (nocturnal stagnant vs convective daytime)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.features.engineering import FeatureEngineer
from src.models.trainer import ModelTrainer, compute_regression_metrics


class ModelEvaluator:
    """
    Evaluates trained AtmosCast models across validation and test chronological splits,
    diagnosing systematic biases, episode-specific errors, and horizon decay.
    """

    EPISODE_THRESHOLD = 120.0  # CPCB Very Poor/Severe threshold for PM2.5 in µg/m³

    def __init__(
        self,
        data_path: str = "data/processed/merged_delhi_ncr_hourly.csv",
        models_dir: str = "models",
        target_pollutant: str = "pm25",
        horizons: List[int] = [24, 48, 72],
    ):
        self.data_path = Path(data_path)
        self.models_dir = Path(models_dir)
        self.target_pollutant = target_pollutant
        self.horizons = horizons
        self.fe = FeatureEngineer(target_pollutant=target_pollutant)
        self.trainer = ModelTrainer(target_pollutant=target_pollutant, models_dir=models_dir)

    def load_and_engineer(self) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
        raw_df = pd.read_csv(self.data_path)
        return self.fe.process_dataset(raw_df, horizons=self.horizons, pollutant=self.target_pollutant)

    def get_split_data(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        horizon: int,
    ) -> Dict[str, Any]:
        target_col = f"target_{self.target_pollutant}_h{horizon}"
        X_train, X_val, X_test, y_train, y_val, y_test = self.trainer.chronological_split(
            df=df, feature_cols=feature_cols, target_col=target_col
        )
        return {
            "X_train": X_train,
            "X_val": X_val,
            "X_test": X_test,
            "y_train": y_train,
            "y_val": y_val,
            "y_test": y_test,
        }

    def evaluate_all_models(
        self,
        df: pd.DataFrame,
        feature_tiers: Dict[str, List[str]],
    ) -> pd.DataFrame:
        """
        Loads all 27 models from disk and compiles evaluation metrics on both Validation and Test sets.
        """
        records = []
        model_types = ["persistence", "random_forest", "xgboost"]

        for h in self.horizons:
            for tier_name, features in feature_tiers.items():
                split_data = self.get_split_data(df, features, h)
                X_val, y_val = split_data["X_val"], split_data["y_val"]
                X_test, y_test = split_data["X_test"], split_data["y_test"]

                for m_type in model_types:
                    artifact_path = self.models_dir / f"{m_type}_{tier_name}_{self.target_pollutant}_h{h}.joblib"
                    if not artifact_path.exists():
                        continue

                    pkg = joblib.load(artifact_path)
                    model = pkg["model"]

                    # Validation predictions
                    val_preds = model.predict(X_val)
                    val_metrics = compute_regression_metrics(y_val.to_numpy(), val_preds)

                    # Test predictions
                    test_preds = model.predict(X_test)
                    test_metrics = compute_regression_metrics(y_test.to_numpy(), test_preds)

                    # Mean Bias Error (MBE): positive = overprediction, negative = underprediction
                    val_mbe = float(np.mean(val_preds - y_val.to_numpy()))
                    test_mbe = float(np.mean(test_preds - y_test.to_numpy()))

                    records.append({
                        "horizon": h,
                        "tier_name": tier_name,
                        "model_type": m_type,
                        "artifact_path": str(artifact_path),
                        "val_mae": val_metrics["MAE"],
                        "val_rmse": val_metrics["RMSE"],
                        "val_r2": val_metrics["R2"],
                        "val_mape": val_metrics["MAPE"],
                        "val_mbe": round(val_mbe, 2),
                        "test_mae": test_metrics["MAE"],
                        "test_rmse": test_metrics["RMSE"],
                        "test_r2": test_metrics["R2"],
                        "test_mape": test_metrics["MAPE"],
                        "test_mbe": round(test_mbe, 2),
                    })

        return pd.DataFrame(records)

    def select_best_models_on_validation(self, eval_df: pd.DataFrame) -> pd.DataFrame:
        """
        Selects the single best model configuration per forecast horizon
        based strictly on validation RMSE, preventing test set tuning leakage.
        """
        best_rows = []
        for h in self.horizons:
            sub = eval_df[eval_df["horizon"] == h].sort_values(by="val_rmse").reset_index(drop=True)
            best_rows.append(sub.iloc[0])
        return pd.DataFrame(best_rows)

    def evaluate_episode_performance(
        self,
        df: pd.DataFrame,
        best_models_df: pd.DataFrame,
        feature_tiers: Dict[str, List[str]],
    ) -> pd.DataFrame:
        """
        Evaluates predictions during acute severe pollution episodes (actual PM2.5 >= 120 µg/m³)
        versus standard conditions, quantifying peak compression and systematic underprediction.
        """
        episode_records = []

        for _, row in best_models_df.iterrows():
            h = int(row["horizon"])
            tier = row["tier_name"]
            m_type = row["model_type"]
            features = feature_tiers[tier]

            pkg = joblib.load(row["artifact_path"])
            model = pkg["model"]

            split_data = self.get_split_data(df, features, h)
            X_test, y_test = split_data["X_test"], split_data["y_test"]
            test_preds = model.predict(X_test)
            y_arr = y_test.to_numpy()

            # Episode mask
            is_episode = y_arr >= self.EPISODE_THRESHOLD
            normal_mask = ~is_episode

            for regime, mask in [("Severe Episode (>= 120 µg/m³)", is_episode), ("Moderate / Standard (< 120 µg/m³)", normal_mask)]:
                if mask.sum() == 0:
                    continue
                y_sub = y_arr[mask]
                pred_sub = test_preds[mask]
                mae = float(mean_absolute_error(y_sub, pred_sub))
                rmse = float(np.sqrt(mean_squared_error(y_sub, pred_sub)))
                mbe = float(np.mean(pred_sub - y_sub))

                episode_records.append({
                    "horizon": f"{h}h",
                    "model": f"{m_type.title()} ({tier})",
                    "regime": regime,
                    "sample_count": int(mask.sum()),
                    "mean_actual": round(float(y_sub.mean()), 1),
                    "mean_predicted": round(float(pred_sub.mean()), 1),
                    "mae": round(mae, 2),
                    "rmse": round(rmse, 2),
                    "mbe": round(mbe, 2),
                })

        return pd.DataFrame(episode_records)

    def evaluate_regimes(
        self,
        df: pd.DataFrame,
        best_models_df: pd.DataFrame,
        feature_tiers: Dict[str, List[str]],
    ) -> pd.DataFrame:
        """
        Evaluates diurnal/meteorological regimes on test set:
        - Stagnant Nocturnal (IST hours 22:00-06:00 & wind < 5 km/h)
        - Convective Afternoon (IST hours 12:00-16:00)
        - Transition
        """
        regime_records = []

        for _, row in best_models_df.iterrows():
            h = int(row["horizon"])
            tier = row["tier_name"]
            m_type = row["model_type"]
            features = feature_tiers[tier]

            pkg = joblib.load(row["artifact_path"])
            model = pkg["model"]

            split_data = self.get_split_data(df, features, h)
            X_test, y_test = split_data["X_test"], split_data["y_test"]
            test_preds = model.predict(X_test)
            y_arr = y_test.to_numpy()

            # Extract regime from test indices
            test_sub = df.loc[X_test.index]
            hour = pd.to_datetime(test_sub["timestamp_ist"]).dt.hour
            wind = test_sub["wind_speed_10m"]

            is_nocturnal_stagnant = hour.isin([22, 23, 0, 1, 2, 3, 4, 5, 6]) & (wind < 5.0)
            is_convective = hour.isin([12, 13, 14, 15, 16])
            is_transition = ~(is_nocturnal_stagnant | is_convective)

            regimes = [
                ("Nocturnal Stagnant", is_nocturnal_stagnant.to_numpy()),
                ("Convective Daytime", is_convective.to_numpy()),
                ("Diurnal Transition", is_transition.to_numpy()),
            ]

            for reg_name, mask in regimes:
                if mask.sum() == 0:
                    continue
                y_sub = y_arr[mask]
                p_sub = test_preds[mask]
                mae = float(mean_absolute_error(y_sub, p_sub))
                rmse = float(np.sqrt(mean_squared_error(y_sub, p_sub)))
                mbe = float(np.mean(p_sub - y_sub))

                regime_records.append({
                    "horizon": f"{h}h",
                    "model": f"{m_type.title()} ({tier})",
                    "regime": reg_name,
                    "sample_count": int(mask.sum()),
                    "mae": round(mae, 2),
                    "rmse": round(rmse, 2),
                    "mbe": round(mbe, 2),
                })

        return pd.DataFrame(regime_records)
