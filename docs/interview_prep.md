# AtmosCast — Technical Interview Preparation Notes

## SIH26082 Problem Statement Understanding

**Q: What problem does AtmosCast solve?**  
AtmosCast addresses SIH Problem Statement SIH26082: *Air Pollution–Weather Coupled Forecasting System*. Delhi NCR suffers some of the world's worst winter air quality, driven by boundary layer compression, wind speed collapse, secondary aerosol formation, and regional stubble burning. We built an end-to-end ML platform that couples ground-level pollution sensor data with ERA5/NWP meteorology to forecast PM2.5 concentrations at 24, 48, and 72-hour lead times across 6 Delhi NCR monitoring stations.

---

## Architecture & Design Decisions

**Q: Why three feature tiers instead of one model?**  
Ablation study design. Tier 1 (pollution history only, 38 features) establishes the baseline predictive power of autocorrelation. Tier 2 (+ surface meteorology, 59 features) quantifies the marginal value of wind, temperature, and humidity. Tier 3 (+ coupled atmospheric diagnostics, 65 features) adds dew point depression, stagnation index, and atmospheric inversion proxies. This lets us answer the scientific question: *how much does each data source contribute?*

**Q: Why direct multi-horizon forecasting rather than recursive rollout?**  
Recursive rollout compounds errors — a prediction error at t+1 propagates to t+2, t+3, all the way to t+72. After 72 compounding steps on a small dataset, the recursive trajectory would diverge rapidly. Direct forecasting trains a separate model for each horizon h ∈ {24, 48, 72}:
$$\hat{y}_{t+h} = f_h(X_t)$$
Each model independently learns the statistical patterns relevant to that specific lead time — short-term inertia for 24h, meteorological steering for 72h.

**Q: Why XGBoost over LSTM?**  
Two reasons: (1) *Data volume* — the current dataset covers only 7 days (~117 training samples per station). An LSTM requires thousands of sequences for stable training; on 7-day data it severely overfits. (2) *Explainability* — XGBoost supports TreeSHAP (exact cooperative game-theoretic attribution), making every forecast interpretable. LSTM explanations require approximate gradient-based methods that are less scientifically rigorous.

**Q: Why are the R² values negative?**  
This is the most important honest answer in the entire project. Negative R² means the model performs worse than a naive mean predictor on this test set — but *this is not a software bug*. The test set coincides with the January 5–7, 2024 peak smog episode, an unprecedented extreme event where PM2.5 reached 475 µg/m³ at Anand Vihar. Tree-based regressors cannot extrapolate above their training maximum (this is called *peak compression*). The 7-day training window never showed concentrations this extreme, so the model underestimates the peak by ~87 µg/m³. The correct response is not to hide this — it's to explain it and document that expanding the training window to multi-month records is the primary future work item.

---

## Data & Science

**Q: How did you handle data leakage?**  
Three measures: (1) All rolling statistics and lag features are computed with `.shift(1)` — the feature at time t uses only data from t-1 and earlier. (2) Train/validation/test split is strictly chronological by time index, never shuffled. (3) Imputers, scalers, and rolling window statistics are fitted exclusively on the training partition and applied to validation/test.

**Q: Where does the meteorological data come from?**  
Open-Meteo's Historical Weather API, which serves ERA5 reanalysis data from ECMWF. It provides 2m temperature, relative humidity, dew point, surface pressure, 10m wind speed/direction, wind gusts, and precipitation — all at 1-hour resolution, free of charge, with no API key required, under CC BY 4.0.

**Q: How is the CPCB AQI calculated?**  
Exact statutory implementation: (1) For each pollutant p with a 24h average concentration C_p, compute sub-index I_p using piecewise linear interpolation across official CPCB breakpoints. (2) Overall AQI = max(I_PM2.5, I_PM10, I_NO2, I_O3, I_SO2, I_CO). The maximum sub-index rule (not an average) is the statutory requirement — the CPCB mandates the "prominent pollutant" with the highest sub-index drives the overall AQI category.

**Q: What does the SHAP analysis tell us?**  
On the 48-hour XGBoost Tier 2 model: 52.1% of predictive variance comes from pollution history (lags and rolling statistics), 46.5% from surface meteorology, and 1.3% from temporal/diurnal features. The single most important feature is `relative_humidity_2m` (mean |SHAP| = 8.871 µg/m³), reflecting secondary inorganic aerosol formation at high humidity. Wind direction sine encoding captures the northwest transport corridor from Punjab stubble burning regions. **Important caveat:** SHAP measures statistical association within the model, not physical causality.

**Q: Can you attribute pollution to stubble burning?**  
No — not without HYSPLIT backward trajectory modeling. NASA FIRMS data shows fire hotspots in Punjab and Haryana, but connecting a specific fire to elevated Delhi PM2.5 requires computing the air mass origin trajectory backward in time. We clearly document this limitation in the explainability report and UI.

---

## Machine Learning

**Q: How did you select the best model?**  
Validation set performance (not test set). The validation set is the second 15% chronological slice (before the test set). We ranked all 27 models by validation RMSE per horizon and selected: 24h → Persistence Tier 1, 48h → Random Forest Tier 3, 72h → Persistence Tier 1. The test set was evaluated exactly once per horizon, only after model selection was finalized.

**Q: Why does Persistence outperform ML at 24h and 72h?**  
During sustained stagnation episodes — which is exactly when the test set falls — pollution levels remain elevated across consecutive days. "Assume tomorrow looks like today" (persistence) is a surprisingly competitive baseline during multi-day smog events. ML models bring value when conditions are changing; during the flat plateau of a severe episode, autocorrelation dominates.

**Q: How did you compute uncertainty intervals?**  
Empirical 90% prediction intervals:
$$\text{PI}_{90\%}(h) = \hat{y}_{t+h} \pm 1.645 \times \text{RMSE}_h \times \sqrt{h/48}$$
The RMSE comes from held-out validation metrics. The √(h/48) scaling factor acknowledges that forecast uncertainty grows with lead time — wider bands at 72h than at 24h.

---

## Implementation Quality

**Q: How did you prevent circular imports?**  
Verified with a DFS traversal of the import DAG across all 46 source modules. No circular dependency was found. Import hierarchy: `src.utils` → `src.features` → `src.models` → `src.forecasting` → `src.ui` (one-directional).

**Q: How many tests do you have and what do they cover?**  
114 tests across 10 test modules (all passing):
- `test_project_setup.py` (7): directory structure, config loading
- `test_app_startup.py` (4): Streamlit AppTest for all 8 pages
- `test_data_collection.py` (6): API failures, timeouts, partial failures
- `test_preprocessing.py` (8): UTC alignment, forward-fill, clipping
- `test_eda.py` (11): EDA functions and chart generation
- `test_modeling.py` (15): Feature engineering, training, serialization
- `test_evaluation.py` (13): MAE/RMSE/R² computation, report generation
- `test_explainability.py` (10): SHAP attribution, group shares
- `test_forecasting.py` (13): AQI breakpoints, 72h trajectory length, errors
- `test_audit_and_hardening.py` (27): API resilience, offline inference, CPCB bounds

**Q: How does the app behave if the internet is unavailable?**  
Fully offline operation. All dashboard pages use the committed processed dataset and pre-trained model artifacts — no network calls are made at runtime. API calls only happen in the separate data collection pipeline (`src/data_collection/`), which is never triggered at dashboard startup.

---

## Deployment

**Q: Why did you commit model artifacts to git?**  
The 27 `.joblib` files total 11.5 MB — well within GitHub's 100 MB/file and 1 GB/repo limits. For Streamlit Community Cloud, there is no attached persistent storage; the only way to provide pre-trained artifacts is to commit them to the repository. The alternative (training at startup) would take 2–5 minutes and waste cloud compute on every cold start. Committing artifacts is the correct approach for this project size.

**Q: How are API keys handled securely?**  
Three-layer protection: (1) `.env` is in `.gitignore` and confirmed absent from git. (2) `.env.example` has blank placeholder values only. (3) On Streamlit Cloud, secrets are injected via the platform's encrypted Secrets manager and read with `st.secrets` — they never touch the filesystem. The `config.py` module reads environment variables first, then Streamlit secrets, then falls back to defaults.

---

## Limitations Acknowledgment (Critical for SIH Presentation)

Always lead with limitations — it demonstrates scientific maturity:

1. **7-day training window** is the most critical limitation. Seasonal variability, monsoon-to-winter transitions, and multi-year pollution cycles cannot be learned from one week of data.
2. **Peak compression** in tree models prevents accurate extreme-event forecasting above the training maximum.
3. **No real-time meteorology** — the forecast engine uses historical weather for demonstration. Operational deployment requires live NWP feed.
4. **No HYSPLIT** — cannot formally attribute pollution episodes to stubble burning sources.
5. **LSTM deferred** — requires 3+ months of training data for stable recurrent network training.

---

*AtmosCast v1.0 | SIH26082 | Phase 12 Final*
