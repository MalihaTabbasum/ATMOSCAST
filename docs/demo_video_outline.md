# AtmosCast — Demo Video Outline

**Recommended Duration:** 5–7 minutes  
**Format:** Screen recording with voiceover  
**Tool:** OBS Studio or Loom (free)  
**Resolution:** 1920×1080 minimum

---

## Video Structure

### [0:00–0:30] Opening Hook — The Problem

**Visuals:** Satellite image of Delhi smog + PM2.5 chart showing 475 µg/m³ spike

**Script:**
> "On January 7th, 2024, PM2.5 concentrations at Anand Vihar, Delhi, hit 475 micrograms per cubic meter — 31 times the WHO safe limit. This is not an isolated event. Delhi's winter smog crisis repeats every year, driven by atmospheric boundary layer collapse, stagnant winds, and agricultural fires. Existing public AQI tools show you what pollution is *now* — but not where it's going. That's the problem AtmosCast solves."

---

### [0:30–1:15] Project Introduction

**Visuals:** AtmosCast Overview page loading in browser

**Script:**
> "AtmosCast is a weather-aware air pollution forecasting platform built for SIH Problem Statement SIH26082. It couples ground-based pollution sensor data from 6 Delhi NCR monitoring stations with ERA5 meteorological reanalysis to predict PM2.5 concentrations 24, 48, and 72 hours into the future. The system is fully explainable — every forecast traces back to its atmospheric drivers."

**Show:**
- Overview page KPI cards (latest PM2.5, AQI status pill)
- 6-station selector in sidebar
- Navigation menu

---

### [1:15–2:00] Air Quality Monitoring

**Visuals:** Air Quality Monitoring page — select Anand Vihar

**Script:**
> "The Air Quality Monitoring page shows historical pollution time-series for the selected station. Here we're looking at Anand Vihar, the highest-pollution station in our dataset. The red dashed line is the Indian CPCB 24-hour PM2.5 standard of 60 micrograms per cubic meter. During our 7-day observation window in January 2024, every single hour exceeded this standard."

**Show:**
- PM2.5 time-series with CPCB threshold line
- Multi-pollutant dropdown switching (PM2.5 → PM10)
- Station switching to see spatial variation

---

### [2:00–3:00] 72-Hour Forecast Engine

**Visuals:** 72-Hour Forecast page

**Script:**
> "The forecasting engine uses XGBoost trained on 59 coupled pollution-meteorology features to generate direct 72-hour predictions without recursive rollout. Direct forecasting avoids error compounding — each horizon has its own dedicated model. We also compute empirical 90% uncertainty intervals that widen appropriately at longer lead times."

**Show:**
- Click "Generate 72-Hour Forecast" button
- Watch the continuous trajectory chart appear with shaded confidence band
- Highlight the 24h / 48h / 72h milestone cards (PM2.5 prediction + AQI category)
- Point out the forecast trajectory extending beyond historical data

---

### [3:00–4:00] Explainable AI — What's Driving the Forecast?

**Visuals:** Explainable AI page

**Script:**
> "Machine learning models are often black boxes. AtmosCast uses SHAP — Shapley Additive Explanations — based on cooperative game theory, to attribute every prediction to its input features. At the global level: pollution history contributes 52% of the model's predictive power, surface meteorology 46.5%. The single most impactful variable? Relative humidity — when humidity exceeds 85%, secondary inorganic aerosol formation amplifies PM2.5 concentrations dramatically."

**Show:**
- Feature group donut chart (pollution vs weather vs temporal)
- Global SHAP bar chart — top 15 features
- Episode waterfall: "On January 6th, relative humidity at 93% pushed the forecast up by 6.5 µg/m³"
- The plain-language non-technical summary banner

**Important spoken caveat:**
> "One critical clarification: SHAP values measure statistical association inside the model, not physical causality. High SHAP weight on humidity reflects the model's learned pattern — not that humidity physically emits particulate matter."

---

### [4:00–4:45] Model Performance — Honest Evaluation

**Visuals:** Model Performance page

**Script:**
> "Here's where we show our work honestly. The best 24-hour model is Persistence — 'assume tomorrow looks like today' — with a test MAE of 39.5 µg/m³. All R² values are negative, which means the models perform worse than a mean predictor on the test set. This is not a software error — it's because the test period coincides with the most extreme smog episode in the dataset, which the models have never seen during training. We document this clearly rather than hiding it."

**Show:**
- Benchmark table with actual metrics
- Explanation panel about negative R² and peak compression
- 48h horizon where Random Forest beats Persistence

---

### [4:45–5:30] Data Sources & Technical Architecture

**Visuals:** Data Sources & About page, then brief code tour

**Script:**
> "AtmosCast ingests data from four independent sources: OpenAQ v3 for real-time ground sensor data, Open-Meteo for ERA5 weather reanalysis, CAMS EAC4 for atmospheric aerosol products, and NASA FIRMS for satellite fire detection. The entire system spans 12 development phases: data collection, preprocessing, EDA, machine learning, evaluation, explainability, a 72-hour forecasting engine, a Streamlit dashboard, full technical audit with 114 passing tests, and documentation."

**Show:**
- Data sources card grid
- Data quality audit statistics
- Phase roadmap from PROJECT_STATUS.md (briefly)

---

### [5:30–6:00] Deployment & Closing

**Visuals:** Streamlit Cloud deployment URL loading in browser

**Script:**
> "AtmosCast is deployed on Streamlit Community Cloud, accessible at the link in the description. The repository is fully open-source on GitHub with MIT license. All model artifacts, the processed dataset, and comprehensive documentation are committed to the repo — no setup required to explore the code. The system processes 114 automated tests to verify correctness end to end."

**Show:**
- Live deployed URL loading
- GitHub repository front page with README

**Closing:**
> "AtmosCast demonstrates that coupling atmospheric science with interpretable machine learning can help communities anticipate and respond to severe pollution events. The most urgent next step: expanding the training window from 7 days to multiple years — that single change will unlock accurate extreme-event forecasting."

---

## Production Tips

| Element | Recommendation |
|---|---|
| **Audio** | Use a lapel microphone or headset — avoid laptop built-in |
| **Screen** | Dark browser theme or the app's native dark mode |
| **Font size** | Increase browser zoom to 110% for readability |
| **Transitions** | No fancy animations — keep focus on the data |
| **Captions** | Auto-generate with YouTube captions or Rev.com |
| **Background music** | None — this is a technical demonstration |
| **File size** | Export at 1080p H.264, ~200–400 MB for 6 minutes |

---

*AtmosCast v1.0 | SIH26082 Demo Video Outline*
