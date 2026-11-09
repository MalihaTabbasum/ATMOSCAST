# AtmosCast Data Directory Structure

This directory houses raw, processed, and external datasets used for training, validating, and serving the **AtmosCast** forecasting pipeline.

## Directory Layout

```
data/
  ├── raw/         # Untouched, raw downloaded data directly from external APIs or portals
  ├── processed/   # Cleaned, hourly-aligned, merged, and validated datasets
  └── external/    # Supporting external reference tables, station metadata, geo-boundaries
```

## Data Categories

### 1. `data/raw/`
- **Source APIs**:
  - OpenAQ API v3: Historical air quality measurements (`PM2.5`, `PM10`, `O3`, `NO2`, `SO2`, `CO`).
  - CPCB Official Portals: Ground monitoring validation data.
  - Open-Meteo Historical Weather API: Surface meteorology and planetary boundary layer (PBL) height.
  - NASA FIRMS: VIIRS / MODIS satellite active fire detections and fire radiative power (FRP) records.
- **Rule**: Raw files are never modified in place. They remain untouched to preserve experiment provenance.

### 2. `data/processed/`
- **Contents**:
  - Hourly time-series data indexed by UTC / IST (`Asia/Kolkata`).
  - Imputed, outlier-checked, and unified sensor-weather datasets.
  - Ready-to-train chronological feature matrices.
- **Rule**: Processed data must be reproducible purely by running the data processing pipeline (`src/preprocessing/` and `src/features/`).

### 3. `data/external/`
- **Contents**:
  - Geographic boundaries of Delhi NCR and upwind agricultural districts (Punjab & Haryana).
  - CPCB station metadata, coordinates, and historical measurement station codes.
  - NAQI calculation breakpoint reference tables.

## Data Governance & Reproducibility
- Data files in `raw/` and `processed/` are excluded from Git version control via `.gitignore` to maintain a lightweight repository and respect rate/licensing restrictions.
- All pipeline steps are fully scripted and automated via `src/data_collection/` to ensure end-to-end reproducibility.
