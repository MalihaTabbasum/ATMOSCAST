# AtmosCast Data Quality & Preprocessing Report

**Generated:** 2026-11-09 12:48:13 UTC  
**Region:** Delhi National Capital Region (Delhi NCR), India  
**Scope:** Phase 3 Preprocessing, Quality Control, and Station Alignment  

---

## 1. Executive Summary & Row Counts

| Dataset | Raw Records Loaded | Cleaned Records | Deduplicated | Time-Zone Normalized |
|---|---|---|---|---|
| **Air Quality (Pollution)** | 1008 | 1008 | Yes (station + UTC) | UTC & Asia/Kolkata (IST) |
| **Meteorology (Weather)** | 1008 | 1008 | Yes (station + UTC) | UTC & Asia/Kolkata (IST) |
| **Merged Coupled Dataset** | N/A | **1008** | 100% Aligned | Both |

- **Total Stations Harmonized:** 6
- **Date Range Covered:** 2024-01-01 00:00:00+00:00 to 2024-01-07 23:00:00+00:00 (168 discrete hourly timesteps per station)
- **Time Continuity:** Strictly contiguous 1-hour cadence per station.

---

## 2. Station-Wise Record & Coordinate Audit

All coordinates were verified against the official Delhi NCR geographic bounding box ($28.0^\circ\\text{N} - 29.2^\circ\\text{N}, 76.5^\circ\\text{E} - 78.0^\circ\\text{E}$).

| Station ID | Station Name | Hourly Rows | Start Window | End Window | Coordinates |
|---|---|---|---|---|---|
| `delhi_anand_vihar` | **Anand Vihar** | 168 | 2024-01-01 00:00 UTC | 2024-01-07 23:00 UTC | 28.6469°N, 77.3160°E |
| `delhi_igi_airport` | **IGI Airport (T3)** | 168 | 2024-01-01 00:00 UTC | 2024-01-07 23:00 UTC | 28.5562°N, 77.0999°E |
| `delhi_punjabi_bagh` | **Punjabi Bagh** | 168 | 2024-01-01 00:00 UTC | 2024-01-07 23:00 UTC | 28.6740°N, 77.1310°E |
| `delhi_rk_puram` | **R K Puram** | 168 | 2024-01-01 00:00 UTC | 2024-01-07 23:00 UTC | 28.5632°N, 77.1869°E |
| `gurugram_vikas_sadan` | **Vikas Sadan, Gurugram** | 168 | 2024-01-01 00:00 UTC | 2024-01-07 23:00 UTC | 28.4501°N, 77.0263°E |
| `noida_sector_62` | **Sector 62, Noida** | 168 | 2024-01-01 00:00 UTC | 2024-01-07 23:00 UTC | 28.6245°N, 77.3648°E |

---

## 3. Statistical Profiling of Key Variables

Summary statistics across all Delhi NCR monitoring locations:

| Variable | Count | Mean | Std Dev | Min | 25% | 50% (Median) | 75% | Max |
|---|---|---|---|---|---|---|---|---|
| `pm25` | 1008 | 120.71 | 31.80 | 56.60 | 97.25 | 121.30 | 139.82 | 221.20 |
| `pm10` | 1008 | 176.05 | 45.65 | 83.80 | 142.70 | 174.60 | 203.00 | 324.10 |
| `no2` | 1008 | 53.59 | 31.49 | 10.10 | 28.45 | 45.40 | 73.50 | 154.60 |
| `o3` | 1008 | 75.09 | 68.29 | 0.00 | 24.00 | 41.50 | 120.00 | 252.00 |
| `temperature_2m` | 1008 | 10.71 | 3.81 | 4.10 | 7.50 | 10.20 | 13.90 | 18.50 |
| `relative_humidity_2m` | 1008 | 84.82 | 13.34 | 57.00 | 72.00 | 90.00 | 96.00 | 100.00 |
| `wind_speed_10m` | 1008 | 5.63 | 2.03 | 0.00 | 4.00 | 6.00 | 7.00 | 11.40 |

> **Atmospheric Observation:** During the analyzed January 1–7 winter period, mean $\\text{PM}_{2.5}$ reached **120.7 µg/m³** (with peak reaching **221.2 µg/m³**), illustrating the severe particulate matter concentration under shallow boundary layers and winter stagnation.

---

## 4. Missing Value & Imputation Audit

Imputation utilized strictly past-only forward fill (maximum limit: 3 hours) to prevent lookahead data leakage into downstream machine learning models.

| Variable | Total Rows | Null Count | Null % | Status |
|---|---|---|---|---|
| `pm25` | 1008 | 0 | 0.00% | Clean / Imputed |
| `pm10` | 1008 | 0 | 0.00% | Clean / Imputed |
| `no2` | 1008 | 0 | 0.00% | Clean / Imputed |
| `o3` | 1008 | 0 | 0.00% | Clean / Imputed |
| `temperature_2m` | 1008 | 0 | 0.00% | Clean / Imputed |
| `relative_humidity_2m` | 1008 | 0 | 0.00% | Clean / Imputed |
| `wind_speed_10m` | 1008 | 0 | 0.00% | Clean / Imputed |
| `surface_pressure` | 1008 | 0 | 0.00% | Clean / Imputed |
| `precipitation` | 1008 | 0 | 0.00% | Clean / Imputed |

---

## 5. Quality Control Audit Log & Outlier Investigation

- **Total QC Events Handled:** 0
- **Event Breakdown:**
No quality issues detected.

### Scientific Outlier Policy:
1. **Physical Impossibility vs. Severe Episodes:** Negative pollutant concentrations were clipped to zero. Extreme high readings up to 1,200 µg/m³ for $\\text{PM}_{2.5}$ were preserved as genuine atmospheric episode phenomena (severe smog and temperature inversion events) rather than dropped.
2. **Particulate Matter Ratio Check:** PM2.5 <= PM10 constraint enforced. In instances of slight sensor inversion due to optical counters, PM10 was capped to PM2.5 and logged.
3. **No Random Replacement:** Zero synthetic random numbers were injected.

---

## 6. Generated Output Files

The following standardized artifacts have been written to `data/processed/`:
1. `data/processed/pollution_cleaned.csv`
2. `data/processed/weather_cleaned.csv`
3. `data/processed/merged_delhi_ncr_hourly.csv`
4. `data/processed/qc_audit_log.csv`
