# AtmosCast — Deployment Guide

## Streamlit Community Cloud Deployment

This document provides complete, step-by-step instructions for deploying
AtmosCast to **Streamlit Community Cloud** (the free tier at share.streamlit.io).

> [!IMPORTANT]
> AtmosCast requires no active internet connection to run its core dashboard.
> All model artifacts (27 × `.joblib` files, 11.5 MB total) and the processed
> dataset (247 KB) are committed to the repository and will be available on
> Streamlit Cloud automatically after pushing.

---

## Prerequisites

| Requirement | Minimum | Notes |
|---|---|---|
| Python | 3.11+ | Streamlit Cloud defaults to 3.11 |
| Streamlit account | Free | sign up at share.streamlit.io |
| GitHub account | Free | Repository must be public for free tier |
| Repository size | < 1 GB | Current repo ≈ 13 MB |

---

## Part 1 — Prepare the GitHub Repository

### Step 1.1 — Verify no secrets are tracked

```bash
# Confirm .env is not in git
git ls-files .env

# Confirm no API keys in staged/committed files
git grep -i "api_key\s*=\s*['\"][a-zA-Z0-9]" -- "*.py" "*.yaml" "*.toml"
```

Both commands should return empty output.

### Step 1.2 — Verify model artifacts are tracked

```bash
git ls-files models/ | grep ".joblib" | wc -l
# Expected output: 27
```

### Step 1.3 — Verify processed dataset is tracked

```bash
git ls-files data/processed/
# Expected: data/processed/merged_delhi_ncr_hourly.csv
```

### Step 1.4 — Push all changes to GitHub

```bash
git push origin main
```

### Step 1.5 — Confirm repository is public

In GitHub → Settings → Danger Zone → Change repository visibility → **Public**  
(Required for the free tier of Streamlit Community Cloud)

---

## Part 2 — Deploy to Streamlit Community Cloud

### Step 2.1 — Sign in to Streamlit Cloud

1. Open https://share.streamlit.io/
2. Click **Sign in with GitHub**
3. Authorize Streamlit to access your GitHub repositories

### Step 2.2 — Create a new app deployment

1. Click **New app**
2. Fill in the deployment form:

| Field | Value |
|---|---|
| **Repository** | `<your-username>/AtmosCast` |
| **Branch** | `main` |
| **Main file path** | `app.py` |
| **App URL** | Choose a name, e.g. `atmoscast-delhi` |

3. Click **Advanced settings** (optional — for API credentials)
4. Click **Deploy**

### Step 2.3 — Monitor the build log

Streamlit Cloud will:
1. Clone the repository
2. Create a fresh Python 3.11 virtual environment
3. Run `pip install -r requirements.txt`
4. Launch `streamlit run app.py`

**Expected build time:** 3–8 minutes (first deployment installs ~16 packages).  
**Expected status:** `Running ✓` within 10 minutes.

### Step 2.4 — Add optional API credentials (Secrets)

If you want live data collection (OpenAQ / NASA FIRMS):

1. In your deployed app → **⋮ menu** (top-right) → **Settings** → **Secrets**
2. Paste the following (replace empty strings with your actual keys):

```toml
OPENAQ_API_KEY = "your_openaq_key_here"
NASA_FIRMS_MAP_KEY = "your_firms_key_here"
```

3. Click **Save** — the app restarts automatically.

> **Without any secrets configured, AtmosCast runs fully in offline demonstration
> mode using the committed processed dataset and trained model artifacts.**

---

## Part 3 — Verify the Deployed Application

### Step 3.1 — Confirm all 8 pages load

After deployment, manually test each navigation item:

- [ ] **1. Overview** — KPI cards render, CPCB AQI status pill appears
- [ ] **2. Air Quality Monitoring** — PM2.5 / PM10 / NO2 / O3 time-series charts load
- [ ] **3. 72-Hour Forecast** — Clicking "Generate 72-Hour Forecast" produces predictions
- [ ] **4. Weather Analysis** — Temperature, humidity, wind charts render
- [ ] **5. Pollution Episode Analysis** — Jan 5–6 2024 episode charts load
- [ ] **6. Model Performance** — Benchmark table loads from model_registry.json
- [ ] **7. Explainable AI** — SHAP global importance and waterfall charts render
- [ ] **8. Data Sources & About** — Project information page loads

### Step 3.2 — Confirm station switching

Change the **Selected Monitoring Station** in the sidebar — all pages should update
to reflect the new station without errors.

### Step 3.3 — Check for console errors

In the Streamlit Cloud dashboard → **Logs** tab — look for any `ERROR` or
`Exception` lines. Common first-deployment issues and fixes are listed in
[Part 5 — Troubleshooting](#part-5--troubleshooting).

---

## Part 4 — Local Testing Before Deployment

To simulate the cloud environment locally (clean virtual environment):

```bash
# 1. Create a clean environment
python -m venv .venv_clean
.venv_clean\Scripts\activate        # Windows
# source .venv_clean/bin/activate   # macOS/Linux

# 2. Install exactly what the cloud will install
pip install -r requirements.txt

# 3. Set working directory to project root (critical — Streamlit Cloud CWD = repo root)
cd path/to/AtmosCast

# 4. Run the app
streamlit run app.py

# 5. Run the full test suite
pytest -v
```

**Expected:** All 114 tests pass, app loads at http://localhost:8501.

---

## Part 5 — Troubleshooting

### App fails with `MissingModelError`

```
MissingModelError: Required model artifact not found at: models/xgboost_tier2_...
```

**Cause:** Model `.joblib` files are not tracked in git.  
**Fix:** Ensure the `.gitignore` exceptions are present and push:
```bash
git add models/*.joblib models/model_registry.json
git commit -m "Add trained model artifacts for cloud deployment"
git push origin main
```

---

### App fails with `FileNotFoundError` on dataset

```
FileNotFoundError: ... merged_delhi_ncr_hourly.csv
```

**Cause:** Processed data file not tracked in git.  
**Fix:**
```bash
git add data/processed/merged_delhi_ncr_hourly.csv
git commit -m "Add processed dataset for deployment"
git push origin main
```

---

### Build fails with `ModuleNotFoundError`

```
ModuleNotFoundError: No module named 'shap'
```

**Cause:** `requirements.txt` is missing a dependency.  
**Fix:** Verify `requirements.txt` is committed and all packages are listed:
```bash
pip install -r requirements.txt  # test locally first
git add requirements.txt
git push origin main
```

---

### App loads but 72-Hour Forecast page shows an error

```
InsufficientContextError: Need at least 24 hours of history
```

**Cause:** The dataset slice for the selected station is too small.  
**Fix:** This is expected behavior when a station has fewer than 24 observations.
Switch to **Anand Vihar** (highest data coverage) for demonstration.

---

### SHAP waterfall chart not rendering

**Cause:** The XGBoost Tier 2 48h model artifact may be missing.  
**Verification:**
```bash
git ls-files models/ | grep "xgboost_tier2_pollution_and_weather_pm25_h48"
```
If empty, re-add model files and push.

---

### Secret variables not being picked up

**Cause:** Streamlit secrets must be in TOML format, not `.env` format.  
**Fix:** In Streamlit Cloud Secrets, use:
```toml
OPENAQ_API_KEY = "your_key_here"   # ← correct TOML format
```
Not:
```
OPENAQ_API_KEY=your_key_here       # ← .env format, will NOT work
```

---

## Part 6 — Architecture for Cloud Deployment

```
Streamlit Community Cloud
├── Worker Container (Python 3.11, Ubuntu)
│   ├── pip install -r requirements.txt (at build time)
│   ├── streamlit run app.py (entrypoint)
│   │
│   ├── data/processed/merged_delhi_ncr_hourly.csv   ← from git
│   ├── models/*.joblib (27 files)                   ← from git
│   ├── models/model_registry.json                   ← from git
│   ├── config/settings.yaml                         ← from git
│   └── .streamlit/config.toml                       ← from git
│
├── Secrets (injected as environment variables)
│   ├── OPENAQ_API_KEY     (optional)
│   └── NASA_FIRMS_MAP_KEY (optional)
│
└── Outbound network (for optional live API calls)
    ├── api.openaq.org       (if OPENAQ_API_KEY set)
    ├── firms.modaps.eosdis.nasa.gov (if NASA_FIRMS_MAP_KEY set)
    └── archive-api.open-meteo.com   (no key required)
```

---

## Part 7 — Limitations of Streamlit Community Cloud

| Limitation | Impact on AtmosCast |
|---|---|
| **1 GB memory limit** | SHAP computation on large datasets could exceed this. Current dataset (1,008 rows) is well within limits. |
| **Sleeps after 7 days inactivity** | App needs one manual visit or ping to wake up — first load takes ~20s |
| **No persistent file writes** | AtmosCast does not write files at runtime (all artifacts pre-committed) — no impact |
| **Public repository required (free tier)** | Repository must be public. No private data or secrets should be committed (already compliant). |
| **Cold starts** | First load after sleep: ~15–20s. Subsequent loads: ~2–3s (Streamlit caching). |

---

## Part 8 — Reproducible Training Instructions

If you need to regenerate the model artifacts from scratch:

```bash
# Step 1: Collect fresh data (requires API keys in .env)
python -m src.data_collection.pipeline

# Step 2: Preprocess and merge
python -m src.preprocessing.pipeline

# Step 3: Train all 27 models
python scripts/train_models.py

# Step 4: Verify
python -m pytest tests/ -v
```

**Expected training time:** 2–5 minutes on a modern laptop  
**Expected output:** 27 × `.joblib` files in `models/`, plus updated `model_registry.json`

---

## Repository Checklist Before Deployment

- [x] `app.py` — main entrypoint, uses `Path(__file__)`-relative resolution
- [x] `requirements.txt` — all 16 dependencies listed
- [x] `.streamlit/config.toml` — theme and server settings
- [x] `.streamlit/secrets.toml.example` — secrets template (no actual values)
- [x] `config/settings.yaml` — no hardcoded API keys
- [x] `data/processed/merged_delhi_ncr_hourly.csv` — 247 KB dataset committed
- [x] `models/*.joblib` (27 files) — 11.5 MB model artifacts committed
- [x] `models/model_registry.json` — normalized forward-slash paths
- [x] `.gitignore` — excludes `.env`, `.streamlit/secrets.toml`
- [x] No hardcoded absolute paths in any source file
- [x] No API keys in any committed file
- [x] 114/114 tests passing

---

*AtmosCast v1.0 — Phase 12: Deployment Preparation*
