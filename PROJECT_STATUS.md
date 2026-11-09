# AtmosCast Project Status & Tracking

## Project Overview
**AtmosCast — Weather-Aware Air Pollution Forecasting System (Delhi NCR Focus)**  
*Based on SIH Problem Statement SIH26082: Air Pollution–Weather Coupled Forecasting System.*  
AtmosCast is an end-to-end Machine Learning and atmospheric intelligence platform designed to forecast air pollutants (`PM2.5`, `PM10`, `O3`, `NO2`) over 24, 48, and 72-hour horizons across Delhi NCR monitoring stations by coupling historical pollution trends with boundary-layer meteorology, atmospheric inversion indicators, and regional agricultural stubble fire activity.

---

## 12-Phase Development Roadmap

| Phase | Phase Name | Status |
|---|---|---|
| **PHASE 01** | **Project Initialization & Architecture Setup** | **COMPLETED** |
| **PHASE 02** | **Multi-Agency Real-World Data Collection** | **COMPLETED** |
| **PHASE 03** | **Data Harmonization, Time-Series Alignment & Quality Control** | **COMPLETED** |
| **PHASE 04** | **Exploratory Data Analysis & Airshed Episodic Profiling** | **COMPLETED** |
| **PHASE 05** | **Boundary-Layer Meteorology & Atmospheric Feature Engineering** | **PENDING** |
| **PHASE 06** | **Baseline Forecasting Models & ML Architecture Setup** | **PENDING** |
| **PHASE 07** | **Gradient-Boosted Multi-Horizon Forecasting Engine (24h, 48h, 72h)** | **PENDING** |
| **PHASE 08** | **Rigorous Horizon-Wise & Seasonal Validation Benchmarking** | **PENDING** |
| **PHASE 09** | **Coupled Atmospheric Feature Ablation Experiments** | **PENDING** |
| **PHASE 10** | **Explainable AI & Atmospheric Sensitivity (SHAP Analysis)** | **PENDING** |
| **PHASE 11** | **Interactive Environmental Intelligence Dashboard (Streamlit UI/UX)** | **PENDING** |
| **PHASE 12** | **Deployment Readiness, Cloud Packaging & GitHub Finalization** | **PENDING** |

---

## Current Status Details

- **Current Phase**: PHASE 04: Exploratory Data Analysis & Airshed Episodic Profiling
- **Phase 04 Status**: **COMPLETED**
- **Current Task**: Completed statistical profiling, time-series visualization, diurnal inversion cycle extraction, meteorology-pollution correlation analysis, extreme episode breakdown (Jan 5–6, 2024), Plotly interactive figure export (8 charts), Jupyter notebook generation (`notebooks/01_exploratory_data_analysis.ipynb`), comprehensive EDA report (`reports/eda_summary_report.md`), and automated test suite (`tests/test_eda.py`).
- **Completed Phases**:
  - [x] **PHASE 01: Project Initialization & Architecture Setup**
  - [x] **PHASE 02: Multi-Agency Real-World Data Collection**
  - [x] **PHASE 03: Data Harmonization, Time-Series Alignment & Quality Control**
  - [x] **PHASE 04: Exploratory Data Analysis & Airshed Episodic Profiling**
- **Pending Phases**:
  - [ ] PHASE 05: Boundary-Layer Meteorology & Atmospheric Feature Engineering
  - [ ] PHASE 06: Baseline Forecasting Models & ML Architecture Setup
  - [ ] PHASE 07: Gradient-Boosted Multi-Horizon Forecasting Engine (24h, 48h, 72h)
  - [ ] PHASE 08: Rigorous Horizon-Wise & Seasonal Validation Benchmarking
  - [ ] PHASE 09: Coupled Atmospheric Feature Ablation Experiments
  - [ ] PHASE 10: Explainable AI & Atmospheric Sensitivity (SHAP Analysis)
  - [ ] PHASE 11: Interactive Environmental Intelligence Dashboard (Streamlit UI/UX)
  - [ ] PHASE 12: Deployment Readiness, Cloud Packaging & GitHub Finalization

---

## Phase 4 EDA Findings & Airshed Characterization

- **Analyzed Dataset**: `data/processed/merged_delhi_ncr_hourly.csv` (1,008 records, 6 CAAQMS stations, Jan 1–7, 2024).
- **Core Statistics & Standards Compliance**:
  - Regional Mean $\text{PM}_{2.5}$: **120.71 µg/m³** (Range: 56.6 to 221.2 µg/m³).
  - Regional Mean $\text{PM}_{10}$: **176.05 µg/m³** (Range: 83.8 to 324.1 µg/m³).
  - WHO Guideline (15 µg/m³) Exceedance Rate: **100.0%** of all 1,008 station-hours.
  - CPCB 24-Hour Standard (60 µg/m³) Exceedance Rate: **99.2%** of all station-hours.
- **Station-Wise Variations**:
  - **Highest Stagnation & Peaks**: Anand Vihar (Mean: $132.8\,\mu\text{g/m}^3$, Max: $221.2\,\mu\text{g/m}^3$) due to heavy diesel transport and highway confluence.
  - **Lowest Relative Baseline**: IGI Airport T3 (Mean: $109.6\,\mu\text{g/m}^3$, Max: $195.0\,\mu\text{g/m}^3$) due to wide open buffer zones and reduced building obstruction.
  - **Regional Synchronicity**: All 6 stations display synchronized episodic peaks, confirming that macro-scale boundary layer dynamics and regional meteorology override micro-scale local sources during winter.
- **Diurnal Dynamics (IST)**:
  - **Morning Rush Peak (08:00–10:00 IST)**: $\text{PM}_{2.5} > 140\,\mu\text{g/m}^3$ as morning vehicular and domestic emissions enter a cold, compressed surface mixing layer.
  - **Afternoon Dispersion Minimum (13:00–16:00 IST)**: $\text{PM}_{2.5}$ drops to diurnal low ($\sim 95\,\mu\text{g/m}^3$) due to solar convective turbulence and boundary layer expansion.
  - **Photochemical Ozone Inversion (13:00–15:00 IST)**: $\text{O}_3$ reaches daily peaks ($140 - 210\,\mu\text{g/m}^3$) in direct opposition to particulate matter, driven by solar UV radiation.
- **Meteorological Drivers (Pearson Correlations with $\text{PM}_{2.5}$)**:
  - **10m Wind Speed ($r = -0.42$)**: Critical threshold identified at $< 5\text{ km/h}$, below which horizontal advection fails and particulate accumulation accelerates.
  - **2m Temperature ($r = -0.38$)**: Drops below $8^\circ\text{C}$ trigger strong nocturnal radiation inversions.
  - **Relative Humidity ($r = +0.35$)**: High humidity ($> 85\%$) facilitates secondary inorganic aerosol formation and hygroscopic growth.
  - **Surface Pressure ($r = +0.28$)**: High synoptic pressure produces atmospheric subsidence, capping vertical dispersion.
- **Scientific Integrity Note**: Correlations reflect physical atmospheric mechanisms (mixing volume, advection, condensation) and do not imply that meteorological variables directly emit pollutants. Seasonal analysis limitations (1-week winter window) are documented transparently without fabricating non-existent annual data.

---

## Files Created & Managed

| File / Path | Purpose |
|---|---|
| `requirements.txt` | Pinned project dependencies |
| `.gitignore` | Excludes raw/processed data, models, reports/figures, cache, and secrets |
| `.env.example` | Environment credentials template |
| `.streamlit/config.toml` | Streamlit server and browser configurations |
| `.streamlit/credentials.toml` | Local non-interactive credential stub |
| `config/settings.yaml` | Master project settings (stations, pollutants, API routes, horizons) |
| `src/utils/config.py` | Configuration reader with path safety and environment overrides |
| `src/utils/visualizations.py` | Professional Plotly visualization suite with navy/teal theme |
| `src/utils/eda_runner.py` | Automated EDA processor and HTML figure exporter |
| `src/utils/generate_notebook.py` | Reproducible EDA Jupyter notebook generator |
| `src/data_collection/*.py` | Multi-source ingestion clients (Open-Meteo, OpenAQ v3, CAMS, FIRMS) |
| `src/preprocessing/loader.py` | Raw data discovery, provenance loading, and schema validation |
| `src/preprocessing/cleaner.py` | Quality control, coordinate checks, bounds enforcement, leakage-safe ffill, and QC logging |
| `src/preprocessing/merger.py` | Station-safe inner joining on `[station_id, timestamp_utc]` and artifact exporter |
| `src/preprocessing/pipeline.py` | Preprocessing orchestrator and automated report generator |
| `notebooks/01_exploratory_data_analysis.ipynb` | Comprehensive interactive EDA notebook with markdown interpretations |
| `reports/eda_summary_report.md` | Formal executive EDA summary report with statistical tables |
| `reports/figures/*.html` | 8 interactive Plotly charts (time-series, diurnal, heatmap, scatters, episodes) |
| `data/processed/merged_delhi_ncr_hourly.csv` | Aligned, coupled analytical dataset (1,008 rows) |
| `tests/test_eda.py` | Unit test suite verifying figures, calculations, notebook, and reports |
| `PROJECT_STATUS.md` | 12-phase tracking log and milestone audit |

---

## Test Results
- **Test Runner**: `pytest 9.2.0` (in `.venv`)
- **Tests Executed**:
  - `tests/test_project_setup.py`: 7 tests passed
  - `tests/test_app_startup.py`: 4 tests passed
  - `tests/test_data_collection.py`: 6 tests passed
  - `tests/test_preprocessing.py`: 8 tests passed
  - `tests/test_eda.py`: 11 tests passed
- **Total Tests Passed**: **36 / 36 (100%)**
- **Tests Failed**: 0

---

## Known Errors & Remaining Issues
- None. Phase 4 EDA and all 8 interactive visualizations are verified, saved, and tested.

---

## Next Recommended Action
Awaiting user approval and prompt to proceed to **PHASE 05: Boundary-Layer Meteorology & Atmospheric Feature Engineering** (lags, rolling statistics, ventilation coefficient, and inversion indicators).
