# Contributing to AtmosCast

Thank you for your interest in contributing to **AtmosCast — Weather-Aware Air Pollution Forecasting System**. We welcome scientific contributions, machine learning improvements, UI enhancements, and test additions.

---

## Code of Conduct & Scientific Integrity

AtmosCast adheres to strict principles of environmental data integrity and empirical reproducibility:
1. **Zero Data Fabrication**: Never synthesize fake pollution measurements or fabricate evaluation metrics.
2. **Zero Future Leakage**: All temporal feature engineering and imputation must strictly look backward ($t \le 0$). Future data must never be used to impute historical feature values.
3. **Statutory Standards**: Follow official Indian Central Pollution Control Board (CPCB) NAQI breakpoint definitions and the maximum sub-index aggregation rule. Never calculate AQI by arithmetic averaging across pollutants.
4. **Physical Plausibility**: All physical variables must remain within verified atmospheric bounds (e.g. non-negative concentrations, $\text{PM}_{2.5} \le \text{PM}_{10}$, relative humidity $0\text{--}100\%$).

---

## Development Workflow

### 1. Fork & Branch
- Fork the repository on GitHub.
- Create a feature or bugfix branch with a descriptive name:
  ```bash
  git checkout -b feature/improved-boundary-layer-scaling
  ```

### 2. Environment Setup
- Python 3.11+ is required (developed and verified on Python 3.13).
- Set up a clean virtual environment and install dependencies:
  ```bash
  python -m venv .venv
  # Windows:
  .venv\Scripts\Activate.ps1
  # Linux/macOS:
  source .venv/bin/activate

  pip install -r requirements.txt
  ```

### 3. Running Tests
Before submitting any changes, all 114 test assertions must pass cleanly:
```bash
pytest -v
```

### 4. Code Quality Standards
- **Typing & Clean Imports**: Ensure all functions have clear type annotations. Eliminate unused imports.
- **Acyclic Architecture**: Never introduce circular imports between modules.
- **No Retraining at Startup**: Frontend dashboard code in `src/ui/` must never call model training routines (`fit()`). All models must be pre-trained and serialized.

### 5. Submitting a Pull Request
- Ensure commit messages are clear and follow standard conventions (e.g. `feat: add boundary layer ventilation feature`, `fix: handle missing dew point calculation`).
- Describe the changes made, relevant test cases added, and physical reasoning behind the modification.
