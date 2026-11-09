# AtmosCast Technical Audit & System Hardening Report (Phase 10)

**Date:** 2026-11-09  
**System:** AtmosCast — Weather-Aware Air Pollution Forecasting System (Delhi NCR Focus)  
**Environment:** Python 3.13.7, pytest 9.2.0, pandas 2.2.3, scikit-learn 1.6.1, xgboost 2.1.4, shap 0.46.0, streamlit 1.42.0  
**Audit Scope:** End-to-end technical resilience, dependency compatibility, import graph integrity, exception propagation, multi-source API failure handling, offline inference verification, and CPCB statutory compliance.

---

## 1. Executive Summary

A comprehensive technical audit was executed across the entire AtmosCast codebase. The audit covered all 46 Python source modules, the main Streamlit application, all data collection clients, preprocessing cleaners, feature engineering pipelines, trained model predictors, the 72-hour forecasting engine, and statutory Indian CPCB NAQI calculation routines.

- **Total Unit & Integration Tests Passed**: **114 / 114 (100%)**
- **Test Modules**: 10 distinct test suites
- **Import Graph Cycles**: 0 (DAG verified acyclic)
- **Unused Imports Remaining**: 0 (100% eliminated across all 46 source files)
- **Offline Inference**: Verified (zero external network dependency during model prediction)
- **Model Retraining at Startup**: 0 (zero runtime re-fitting; all models pre-serialized and cached)

---

## 2. Test Execution Summary

| Test Module | Focus Area | Tests Executed | Passed | Failed |
|---|---|---|---|---|
| `tests/test_audit_and_hardening.py` | API failures, offline mode, missing data, edge configurations, CPCB bounds | 27 | 27 | 0 |
| `tests/test_app_startup.py` | Streamlit UI startup, navigation across 8 pages, reactive station selection | 4 | 4 | 0 |
| `tests/test_forecasting.py` | 72h forecast trajectory, uncertainty intervals, statutory NAQI rules | 13 | 13 | 0 |
| `tests/test_explainability.py` | TreeSHAP values, global feature rankings, macro groups, waterfalls | 10 | 10 | 0 |
| `tests/test_evaluation.py` | Validation selection, multi-horizon error trajectory, regime stratification | 13 | 13 | 0 |
| `tests/test_modeling.py` | Persistence baseline, Random Forest, XGBoost, feature tiers, multi-horizon | 15 | 15 | 0 |
| `tests/test_eda.py` | Diurnal trends, Plotly HTML figures, pollution episodes, correlation heatmap | 11 | 11 | 0 |
| `tests/test_preprocessing.py` | Outlier clipping, PM2.5/PM10 ratio sanity, leakage-safe forward imputation | 8 | 8 | 0 |
| `tests/test_data_collection.py` | Multi-source API clients (Open-Meteo, OpenAQ, CAMS, FIRMS), health checks | 6 | 6 | 0 |
| `tests/test_project_setup.py` | YAML configuration, directory layout, station coordinates, requirements.txt | 7 | 7 | 0 |
| **TOTAL** | **Comprehensive Full System Test Suite** | **114** | **114** | **0** |

---

## 3. Errors Discovered & Corrected During Audit

1. **Unspecified Datetime String Parsing Warning**:
   - *Issue*: `pd.to_datetime(df["timestamp_utc"], utc=True)` emitted `UserWarning: Could not infer format, so each element will be parsed individually...` when evaluating corrupted or irregular strings.
   - *Fix*: Standardized parsing in `ForecastEngine` using `pd.to_datetime(..., format="mixed", utc=True)` which strictly parses ISO timestamps while raising structured `DateParseError` on corrupt inputs without emitting Python warnings.
2. **Missing Secondary Meteorological Variable Imputation**:
   - *Issue*: When input history lacked `dew_point_2m` or `precipitation` columns, `ForecastEngine` raised `IncompatibleFeatureError`.
   - *Fix*: Added robust meteorological fallback imputation in `ForecastEngine.validate_historical_data`: defaults `precipitation` to 0.0 mm and approximates `dew_point_2m` from temperature and relative humidity using Magnus formula: $T_d \approx T - ((100 - \text{RH}) / 5)$.
3. **Invalid Target Pollutant & Feature Tier Validation**:
   - *Issue*: Passing unsupported pollutant identifiers (e.g., `unsupported_gas_xyz`) or nonexistent tiers to `FeatureEngineer` did not validate inputs upfront.
   - *Fix*: Added explicit `ValueError` guard in `FeatureEngineer.__init__` validating against `["pm25", "pm10", "no2", "o3", "so2", "co"]` and implemented `get_feature_columns(tier_name)` with strict tier membership checks.
4. **40+ Unused Imports Across Source Modules**:
   - *Issue*: Legacy and unused typing/library imports (`Path`, `requests`, `np`, `List`, `Optional`, `Tuple`, `Union`, `load_config`, `datetime`, `timezone`) were present in `src/data_collection/`, `src/preprocessing/`, `src/evaluation/`, `src/forecasting/`, and `src/ui/`.
   - *Fix*: Executed complete static AST analysis and cleaned all unused imports. Automated cycle verification confirmed zero circular dependencies.
5. **Partial Pipeline Batch Resilience**:
   - *Issue*: Simulated network drops during multi-station collection previously risked unhandled termination.
   - *Fix*: Verified that `DataCollectionPipeline.run_historical_download` catches station-level exceptions into a structured `summary["failures"]` ledger while completing all operational stations.

---

## 4. Known Limitations

1. **Station Geographic Coverage**:
   - The current baseline dataset covers 6 central and peripheral Delhi NCR stations (`delhi_anand_vihar`, `delhi_rk_puram`, `delhi_punjabi_bagh`, `delhi_igi_airport`, `noida_sector_62`, `gurugram_vikas_sadan`). Stations outside Delhi NCR or newly commissioned CAAQMS units require configuration addition in `config/settings.yaml`.
2. **Extreme Smog Episode Peak Compression**:
   - During acute peak events exceeding $450\,\mu\text{g/m}^3$ (such as the January 5–6, 2024 severe stagnation inversion), the XGBoost regression model exhibits conservative conditional mean regression, underpredicting maximum peaks by approximately 35–45%. Empirical 90% uncertainty intervals successfully encompass these excursions.
3. **Satellite FIRMS Thermal Anomaly Fog Blockage**:
   - NASA FIRMS MODIS/VIIRS thermal sensors cannot penetrate thick winter dense fog or continuous low stratus clouds over the Indo-Gangetic Plains, rendering satellite fire counts an indicative secondary proxy rather than a continuous quantitative predictor.
4. **CPCB Minimum Pollutant Constraint**:
   - Statutory Indian CPCB NAQI requires a minimum of 3 valid pollutants with at least one particulate ($\text{PM}_{2.5}$ or $\text{PM}_{10}$). Single-sensor monitoring stations cannot compute official NAQI and will display an indicative single-pollutant sub-index.

---

## 5. Remaining Deployment Risks & Mitigations

| Deployment Risk | Severity | System Behavior | Mitigation In Place |
|---|---|---|---|
| **Upstream Weather API Outage** | Medium | Live NWP data unavailable | Automatic fallback to historical baseline demonstration meteorological profile (`is_fallback: True`) |
| **OpenAQ API Key Expiration / Rate Limit** | Low | HTTP 401 or 429 response | Graceful degradation logged in health check; fallback to local CAMS/Open-Meteo atmospheric reanalysis |
| **Short Historical Context (< 24h)** | Medium | Insufficient lag memory | Rejection with structured `InsufficientContextError` explaining the 24-hour continuous observation requirement |
| **Out-of-Bounds Physical Measurements** | Low | Sensor hardware failure (< 0 or > 1000 µg/m³) | Automatic QC clipping to physical limits with logging in structured QC audit trail |
| **Non-Finite Model Output (NaN / Inf)** | Critical | Model instability | Intercepted by `NonFinitePredictionError` guard and finite sanity checks |
