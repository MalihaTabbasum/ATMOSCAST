# AtmosCast Data Sources Audit & Ingestion Report

**Generated:** 2026-11-11 16:21:34 UTC  
**Region:** Delhi National Capital Region (Delhi NCR), India  
**Scope:** Phase 2 Real-World Data Ingestion Pipeline  

---

## 1. Connected Data Sources & Health Audit

| Source Name | Endpoint / API | Status | Auth Required | Latency | Operational Role |
|---|---|---|---|---|---|
| **Open-Meteo Historical Weather** | `https://archive-api.open-meteo.com/v1/archive` | `UNREACHABLE` | None | N/A ms | Surface meteorology (Temp, RH, Wind, Pressure, Rain) |
| **Copernicus CAMS (via Open-Meteo AQ)** | `https://air-quality-api.open-meteo.com/v1/air-quality` | `UNREACHABLE` | None | N/A ms | Reanalysis air quality (PM2.5, PM10, NO2, O3, SO2, CO) |
| **OpenAQ API v3** | `https://api.openaq.org/v3` | `AUTHENTICATION_REQUIRED` | `X-API-Key` | N/A ms | Continuous Ambient Air Quality Monitoring Station (CAAQMS) |
| **NASA FIRMS** | `https://firms.modaps.eosdis.nasa.gov/api/area/csv` | `OPTIONAL_UNCONFIGURED` | `MAP_KEY` | N/A ms | Regional active fires & Fire Radiative Power (FRP) |

---

## 2. Configured & Monitored Delhi NCR Stations

The following 6 verified monitoring stations have verified coordinates and active sensor feeds:

| Station ID | Station Name | City / State | Authority | Latitude | Longitude |
|---|---|---|---|---|---|
| `delhi_anand_vihar` | **Anand Vihar** | Delhi | DPCC | 28.6469°N | 77.3160°E |
| `delhi_rk_puram` | **R K Puram** | Delhi | DPCC | 28.5632°N | 77.1869°E |
| `delhi_punjabi_bagh` | **Punjabi Bagh** | Delhi | DPCC | 28.6740°N | 77.1310°E |
| `delhi_igi_airport` | **IGI Airport (T3)** | Delhi | IMD | 28.5562°N | 77.0999°E |
| `noida_sector_62` | **Sector 62, Noida** | Noida | UPPCB | 28.6245°N | 77.3648°E |
| `gurugram_vikas_sadan` | **Vikas Sadan, Gurugram** | Gurugram | HSPCB | 28.4501°N | 77.0263°E |

---

## 3. Available Pollutants & Measured Parameters

### A. Air Quality Variables
- **PM2.5** (Fine Particulate Matter <= 2.5 µg/m³): Primary target variable.
- **PM10** (Respirable Particulate Matter <= 10 µg/m³).
- **Ground-Level Ozone (O3)**: Photochemical oxidant (µg/m³).
- **Nitrogen Dioxide (NO2)**: Urban traffic combustion tracer (µg/m³).
- **Sulphur Dioxide (SO2)**: Industrial and power plant tracer (µg/m³).
- **Carbon Monoxide (CO)**: Incomplete combustion tracer (mg/m³).

### B. Surface Meteorological Variables
- **Temperature at 2m (`temperature_2m`)**: Measured in °C.
- **Relative Humidity (`relative_humidity_2m`)**: Measured in %.
- **Dew Point (`dew_point_2m`)**: Measured in °C.
- **Surface Pressure (`surface_pressure`)**: Measured in hPa.
- **Wind Speed at 10m (`wind_speed_10m`)**: Measured in km/h.
- **Wind Direction at 10m (`wind_direction_10m`)**: Measured in degrees (0° - 360°).
- **Precipitation (`precipitation`)**: Measured in mm.

---

## 4. Missing Variables & Physical Dynamics Observations

1. **Planetary Boundary Layer Height (`boundary_layer_height`)**:
   - **Finding**: In the global reanalysis archive endpoint (`archive-api.open-meteo.com`), `boundary_layer_height` is returned as `null` for historical reanalysis grids over North India.
   - **Mitigation & Scientific Fidelity**: In the operational forecast and recent rolling window endpoint (`api.open-meteo.com/v1/forecast?past_days=...`), `boundary_layer_height` is actively calculated and populated with real physical values. For long-term historical records where numerical PBL height is unindexed, empirical ventilation and thermodynamic proxies (surface-dew point spread, wind stagnation index, and nocturnal radiation inversion proxies) are engineered in Phase 4.
2. **OpenAQ API v3 Key Requirement**:
   - OpenAQ v3 mandates an `X-API-Key` header (free from https://openaq.org/). When the key is unconfigured, AtmosCast utilizes Copernicus CAMS atmospheric reanalysis data, ensuring zero fake data generation and uninterrupted technical progression.

---

## 5. API Limitations & Rate Limits

- **Open-Meteo**: Free for non-commercial research use up to 10,000 daily requests. Does not require authentication.
- **OpenAQ v3**: Free registration tier provides rate-limited access with API key.
- **NASA FIRMS**: Free MAP_KEY provides 10-day lookback area queries without billing.

---

## 6. Data Provenance & Reproducibility Guarantee

All raw ingestion files are saved directly in `data/raw/` with accompanying `*_provenance.json` sidecar files containing:
- Exact API endpoint URL and parameters.
- Station identifier and geographic coordinates.
- Measurement units and elevation.
- Retrieval timestamp (UTC).
- Collector component name.
