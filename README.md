# AtmosCast — Weather-Aware Air Pollution Forecasting System (Delhi NCR Focus)

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost-orange.svg)](https://xgboost.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **SIH Problem Statement Reference: SIH26082**  
> *Air Pollution–Weather Coupled Forecasting System (Delhi NCR Focus)*

---

## 1. Executive Summary & Objective

**AtmosCast** is a machine learning and environmental intelligence system engineered to forecast air pollution dynamics across the National Capital Region (Delhi NCR), India over **24, 48, and 72-hour forecast horizons**.

Air pollution in Delhi NCR is not merely an emissions problem—it is intensely governed by complex meteorology and seasonal atmospheric physics. During winter months, shallow planetary boundary layers, low surface wind speeds, and nocturnal radiation inversions trap pollutants near the surface, while post-monsoon agricultural crop residue burning in upwind states (Punjab & Haryana) injects massive particulate matter pulses into the regional airshed.

AtmosCast investigates and models the empirical relationships between:
- **Pollutants**: $\text{PM}_{2.5}$, $\text{PM}_{10}$, Ground-level Ozone ($\text{O}_3$), $\text{NO}_2$, $\text{SO}_2$, and $\text{CO}$.
- **Boundary-Layer Meteorology**: 2-meter temperature, relative humidity, surface pressure, wind vector (speed & direction), and precipitation.
- **Atmospheric Dynamics**: Planetary Boundary Layer (PBL) height, ventilation coefficients, and atmospheric inversion proxy indicators.
- **Regional Biomass Combustion**: Satellite active fire anomalies and Fire Radiative Power (FRP) from NASA FIRMS.

> **Scientific Integrity & Disclaimer:**  
> AtmosCast couples meteorological variables with machine learning algorithms (XGBoost, Random Forest, Persistence Baseline). It is an **empirical weather-aware statistical forecasting system**, not a complete first-principles coupled chemical transport model (such as WRF-Chem or CMAQ). Photochemical transport simulators involve 3D Navier-Stokes and gas-phase chemical kinetics equations; AtmosCast is designed to provide rapid, actionable, data-driven forecasts while making its physical assumptions transparent.

---

## 2. Atmospheric & Meteorological Mechanisms

Delhi NCR experiences acute episodic pollution due to the coupling of specific meteorology with local and regional emissions:

```
[Upwind Stubble Fires (FRP)] + [Urban Emissions]
                │
                ▼
   [Atmospheric Boundary Layer (PBL)] ──► Height compression traps particulate mass
                │
                ▼
   [Ventilation Coefficient] ─────────► (PBL Height × Wind Speed) indicates dispersion capacity
                │
                ▼
   [Temperature Inversion] ───────────► Thermal gradient caps vertical dilution
                │
                ▼
  [Ground-Level Concentration (PM2.5, PM10, NO2, O3)]
```

- **Ventilation Coefficient ($V_c$)**: Defined as $V_c = \text{PBL Height} \times \text{Wind Speed}$. Low $V_c$ values ($< 2000 \text{ m}^2/\text{s}$) indicate severe stagnation and inability of the airshed to disperse particulates.
- **Atmospheric Temperature Inversion**: Negative vertical temperature lapse rates prevent buoyant vertical mixing, trapping pollutants in the lower boundary layer.
- **Hygroscopic Growth & Secondary Aerosols**: High relative humidity combined with $\text{SO}_2$ and $\text{NO}_x$ precursors accelerates gas-to-particle conversion (secondary inorganic aerosol formation).

---

## 3. Technology Stack

- **Language & Runtime**: Python 3.11+
- **Data Engineering**: Pandas, NumPy, SciPy
- **APIs & Ingestion**: Requests, OpenAQ API v3, Open-Meteo Historical & Forecast APIs, NASA FIRMS
- **Machine Learning**: Scikit-Learn (Baselines & Random Forest), XGBoost (Gradient Boosted Decision Trees), SHAP (Explainable AI / Shapley Additive Explanations)
- **Visualization & UI**: Plotly Interactive Charts, Streamlit Dashboard
- **Testing & Quality Assurance**: Pytest, Unittest
- **Configuration & Environment**: PyYAML, Python-Dotenv

---

## 4. Repository Structure

```
AtmosCast/
├── app.py                     # Streamlit application dashboard entry point
├── requirements.txt           # Pinned production and development dependencies
├── README.md                  # Project overview, scientific context, setup guide
├── .gitignore                 # Exclusion rules for local data, models, cache, secrets
├── .env.example               # Environment credentials template
├── PROJECT_STATUS.md          # Multi-phase progression and verification tracker
├── config/
│   └── settings.yaml          # Master configuration (stations, pollutants, API routes, horizons)
├── data/
│   ├── raw/                   # Pristine raw downloads from APIs (gitignored)
│   ├── processed/             # Cleaned, hourly time-series feature tables (gitignored)
│   ├── external/              # Supporting metadata, geo-bounds, CPCB standards
│   └── README.md              # Data directory protocol and reproducibility notes
├── src/
│   ├── data_collection/       # Multi-source API query clients (OpenAQ, Open-Meteo, FIRMS)
│   ├── preprocessing/         # Time alignment, missing data imputation, outlier QC
│   ├── features/              # Feature engineering (lags, rolling stats, ventilation, inversions)
│   ├── models/                # Persistence, Random Forest, XGBoost model definitions
│   ├── forecasting/           # Multi-horizon (24h, 48h, 72h) inference engine
│   ├── evaluation/            # MAE, RMSE, R2, horizon degradation, seasonal analysis
│   ├── explainability/        # SHAP feature attribution and atmospheric driver interpretation
│   └── utils/                 # Path handling, configuration loader, logging
├── notebooks/                 # Exploratory data analysis and ablation notebooks
├── tests/                     # Automated unit and integration test suite
├── reports/                   # Model performance reports, validation summaries
└── assets/
    └── screenshots/           # UI screenshots and system diagrams
```

---

## 5. Verified Delhi NCR Monitoring Locations

AtmosCast tracks real continuous ambient air quality monitoring stations (CAAQMS) deployed by DPCC, CPCB, IMD, UPPCB, and HSPCB:

| Station ID | Station Name | City / Authority | Latitude | Longitude | Characteristics |
|---|---|---|---|---|---|
| `delhi_anand_vihar` | Anand Vihar | Delhi (DPCC) | 28.6469° N | 77.3160° E | Major inter-state transport hub & industrial hotspot |
| `delhi_rk_puram` | R K Puram | Delhi (DPCC) | 28.5632° N | 77.1869° E | High-density urban residential & administrative corridor |
| `delhi_punjabi_bagh` | Punjabi Bagh | Delhi (DPCC) | 28.6740° N | 77.1310° E | Arterial traffic ring road & mixed residential zone |
| `delhi_igi_airport` | IGI Airport (T3) | Delhi (IMD) | 28.5562° N | 77.0999° E | Open suburban aviation corridor |
| `noida_sector_62` | Sector 62, Noida | Noida (UPPCB) | 28.6245° N | 77.3648° E | Commercial & institutional IT zone in eastern NCR |
| `gurugram_vikas_sadan` | Vikas Sadan | Gurugram (HSPCB) | 28.4501° N | 77.0263° E | Dense civic & commercial hub in southwestern NCR |

---

## 6. Development Roadmap

Development follows a strict phase-by-phase protocol:

- [x] **Workspace Initialization**: Directory scaffolding, configuration design, unit tests, and Streamlit entry point.
- [ ] **Phase 1: Real-World Data Collection**: Ingestion clients for OpenAQ v3, Open-Meteo, CPCB, and NASA FIRMS.
- [ ] **Phase 2: Preprocessing & Harmonization**: Hourly resampling, UTC/IST normalization, and leakage-safe interpolation.
- [ ] **Phase 3: Feature Engineering**: Lagged temporal matrices, ventilation coefficient, temperature inversion indicator, and upwind fire indices.
- [ ] **Phase 4: ML Forecasting Models**: Persistence baseline, Random Forest, and XGBoost for 24h, 48h, and 72h horizons.
- [ ] **Phase 5: Rigorous Evaluation & Ablation**: MAE/RMSE assessment, multi-horizon degradation curves, and 3-tier feature ablation.
- [ ] **Phase 6: Explainable AI**: Global and local SHAP summary analyses to assess physical plausibility of feature weights.
- [ ] **Phase 7: Interactive Dashboard**: Full multi-page Streamlit application with interactive Plotly visualizations.
- [ ] **Phase 8: Deployment & Packaging**: Validation for Streamlit Community Cloud and complete documentation.

---

## 7. Quickstart & Installation

### Prerequisites
- Python 3.11 or higher
- Git

### 1. Clone the repository
```bash
git clone https://github.com/your-username/atmoscast.git
cd atmoscast
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Linux / macOS:
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env and supply your OpenAQ and NASA FIRMS API keys if available.
```

### 5. Run tests
```bash
python -m unittest discover tests
# Or using pytest:
pytest
```

### 6. Launch the Streamlit Dashboard
```bash
streamlit run app.py
```

---

## 8. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
