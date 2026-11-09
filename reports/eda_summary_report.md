# AtmosCast Exploratory Data Analysis (EDA) Report

**Generated:** November 2026  
**Analyzed Period:** January 1, 2024 to January 7, 2024 (Winter Smog Episode)  
**Total Records:** 1,008 hourly observations across 6 Delhi NCR CAAQMS stations  
**Target Variable:** Fine Particulate Matter (PM2.5)  

---

## 1. Executive Summary & Core Insights

Exploratory Data Analysis (EDA) of the coupled air quality and meteorological observations confirms that air pollution across the Delhi National Capital Region is strongly governed by boundary-layer meteorology and atmospheric stagnation during winter:

1. **Persistent Standard Violations:** 100% of the 1,008 station-hours violated the World Health Organization (WHO) 24-hour guideline (15 µg/m³), and **99.2%** of observations exceeded the Indian Central Pollution Control Board (CPCB) 24-hour statutory limit (60 µg/m³).
2. **Inverse Dispersion with Wind Speed ($r = -0.42$):** Wind speeds below 5 km/h represent a critical threshold where particulate matter accumulates rapidly due to the breakdown of horizontal advection.
3. **Diurnal Inversion Dynamics:** Pronounced morning peak (08:00–10:00 IST) and late-night nocturnal buildup reflect diurnal boundary-layer compression and surface temperature inversions.
4. **Photochemical Ozone Anti-Correlation:** Ground-level Ozone exhibits an inverse relationship with particulates and peaks in the early afternoon (13:00–15:00 IST), driven by solar radiation and photochemical reactions involving $\text{NO}_x$ and volatile organic compounds (VOCs).

> **Scientific Integrity Caution:**  
> While strong statistical associations exist between meteorological variables (wind speed, temperature, humidity) and pollutant concentrations, **correlation does not prove causation**. Meteorological indicators act as empirical proxies for atmospheric physical mechanisms (vertical turbulence, planetary boundary layer volume, and chemical secondary aerosol formation) rather than being direct emission sources.

---

## 2. Analysis 1: PM2.5 and PM10 Distribution & Station Variations

- **Interactive Visualizations:**
  - `reports/figures/pm25_timeseries.html`
  - `reports/figures/station_comparison.html`

### Summary Statistics by Station:
| Station | Hourly Obs | PM2.5 Mean | PM2.5 Median | PM2.5 Max | PM10 Mean | PM10 Max | Dominant Land Use |
|---|---|---|---|---|---|---|---|
| **Anand Vihar** | 168 | **132.8 µg/m³** | 134.1 µg/m³ | 221.2 µg/m³ | 194.2 µg/m³ | 324.1 µg/m³ | Inter-state transport hub & commercial |
| **Punjabi Bagh** | 168 | 125.4 µg/m³ | 126.8 µg/m³ | 215.0 µg/m³ | 183.1 µg/m³ | 315.0 µg/m³ | Mixed residential / ring road arterial |
| **R K Puram** | 168 | 120.5 µg/m³ | 121.0 µg/m³ | 210.5 µg/m³ | 175.8 µg/m³ | 308.2 µg/m³ | High-density urban residential |
| **Sector 62, Noida** | 168 | 119.8 µg/m³ | 120.5 µg/m³ | 212.0 µg/m³ | 174.9 µg/m³ | 310.0 µg/m³ | Eastern NCR institutional/tech corridor |
| **Vikas Sadan, Gurugram**| 168 | 116.2 µg/m³ | 117.4 µg/m³ | 208.4 µg/m³ | 169.5 µg/m³ | 301.5 µg/m³ | Southwestern NCR commercial center |
| **IGI Airport (T3)** | 168 | **109.6 µg/m³** | 108.2 µg/m³ | 195.0 µg/m³ | 158.9 µg/m³ | 285.0 µg/m³ | Open suburban aviation corridor |

### Scientific Interpretation:
Anand Vihar consistently registers the highest mean ($132.8\,\mu\text{g/m}^3$) and maximum concentrations ($221.2\,\mu\text{g/m}^3$), consistent with its status as a notorious trans-boundary traffic corridor and unpaved road dust nexus. Conversely, IGI Airport (T3) records the lowest baseline concentrations due to wider open buffers and lower localized building density. However, all six stations follow nearly identical temporal peaks and troughs, demonstrating that regional atmospheric stagnation dominates localized source fluctuations.

---

## 3. Analysis 2: Diurnal Cycles & Photochemical Ozone

- **Interactive Visualization:** `reports/figures/diurnal_cycles.html`

### Observed Hourly Progression (Indian Standard Time):
1. **Nocturnal Inversion Phase (23:00 – 06:00 IST):** Particulate concentrations rise steadily due to radiation inversion capping the surface layer and low surface wind speeds (< 4 km/h).
2. **Morning Rush Hour Peak (08:00 – 10:00 IST):** Traffic emissions inject particulate precursors into a shallow morning mixing layer, driving $\text{PM}_{2.5}$ to its diurnal maximum (mean $> 140\,\mu\text{g/m}^3$).
3. **Afternoon Convective Dilution (12:00 – 16:00 IST):** Solar heating drives thermal turbulence, expanding the planetary boundary layer height. $\text{PM}_{2.5}$ drops to its daily minimum ($95\,\mu\text{g/m}^3$).
4. **Ozone Photochemical Peak (13:00 – 15:00 IST):** Ground-level Ozone displays the exact opposite behavior to particulates, peaking at **140–210 µg/m³** in the afternoon under peak UV solar irradiance.

---

## 4. Analysis 3: Meteorology–Pollution Correlations

- **Interactive Visualizations:**
  - `reports/figures/correlation_heatmap.html`
  - `reports/figures/weather_relationships.html`

### Pearson Correlation Matrix Summary:
| Meteorological Variable | Correlation with PM2.5 | Correlation with PM10 | Physical Atmospheric Mechanism |
|---|---|---|---|
| **Wind Speed 10m** | **-0.42** | **-0.41** | **Ventilation & Advective Dispersion:** Low wind inhibits transport; high wind flushes airshed. |
| **Temperature 2m** | **-0.38** | **-0.36** | **Boundary Layer Height & Inversion:** Cold temperatures suppress buoyant plume rise. |
| **Relative Humidity** | **+0.35** | **+0.33** | **Secondary Inorganic Aerosol Formation:** High humidity accelerates gas-to-particle conversion. |
| **Surface Pressure** | **+0.28** | **+0.29** | **Synoptic Anticyclone Stagnation:** High barometric pressure induces subsidence. |
| **Precipitation** | -0.05 | -0.04 | Wet scavenging (negligible rainfall during this winter week). |

---

## 5. Analysis 4: Severe Smog Episode Investigation (January 5–6, 2024)

- **Interactive Visualization:** `reports/figures/pollution_episode.html`

During January 5–6, Delhi NCR experienced an acute severe episode where $\text{PM}_{2.5}$ surged across all stations from $90\,\mu\text{g/m}^3$ to over **$220\,\mu\text{g/m}^3$** within 18 hours.

### Stagnation Trigger Diagnostics:
- **Wind Stagnation:** Surface wind dropped from $8.4\text{ km/h}$ to calm conditions ($< 1.5\text{ km/h}$).
- **Thermal Inversion:** 2-meter air temperature dropped to **$4.1^\circ\text{C}$**, establishing a strong nocturnal radiation inversion capping the surface boundary layer.
- **Moisture Trapping:** Relative humidity surged to **98–100%**, facilitating hygroscopic growth of sulfate and nitrate particles.

---

## 6. Analysis 5: Seasonal & Monthly Trend Data Limitation Note

- **Data Scope Limitation:**  
  The current cleaned dataset covers 168 contiguous hours (January 1–7, 2024). While this provides high-resolution insights into the peak winter smog phenomenon, **multi-year or full 12-month seasonal comparisons cannot be empirically calculated from a 1-week dataset**.
- **Documented Delhi Seasonal Mechanics:**  
  In compliance with project guidelines, rather than fabricating seasonal curves, Delhi's well-documented annual cycle is noted as:
  - **Monsoon (July–September):** Lowest concentrations ($20 - 45\,\mu\text{g/m}^3$) due to heavy precipitation wet scavenging and deep convective mixing.
  - **Post-Monsoon (October–November):** Extreme episodic spikes ($250 - 600+\,\mu\text{g/m}^3$) driven by upwind agricultural residue burning (Punjab/Haryana) coupled with post-monsoon wind shifts.
  - **Winter (December–January):** Sustained severe baselines ($120 - 250\,\mu\text{g/m}^3$) driven by shallow planetary boundary layer compression, radiation inversions, and low wind speeds.
  - **Pre-Monsoon (March–May):** Dominated by coarse mineral dust ($\text{PM}_{10} > 300\,\mu\text{g/m}^3$) from Thar Desert long-range transport under high convective wind speeds.

---

## 7. Analysis 6: Missing Data Audit

- Across the 1,008 station-hours, missing data rates for all core features (`pm25`, `pm10`, `no2`, `o3`, `temperature_2m`, `relative_humidity_2m`, `wind_speed_10m`, `surface_pressure`, `precipitation`) stand at **0.00%**.
- Data continuity is 100% complete across all 6 stations.
