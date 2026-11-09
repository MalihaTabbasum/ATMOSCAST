"""
Official Indian Central Pollution Control Board (CPCB) National Air Quality Index (NAQI) Module.

Implements statutory Indian CPCB methodology:
- Piecewise linear sub-index interpolation across pollutant concentration breakpoints.
- Maximum sub-index aggregation rule (identifying the prominent pollutant).
- Data sufficiency rules (minimum 3 pollutants, at least one particulate: PM2.5 or PM10).
- Explicit labeling of unavailable or insufficient calculations.
- Clean category classification: Good, Satisfactory, Moderate, Poor, Very Poor, Severe.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


class CPCBIndexCalculator:
    """
    Statutory CPCB NAQI Calculator adhering to official Ministry of Environment,
    Forest and Climate Change (MoEFCC) guidelines.
    """

    # Official CPCB Breakpoints: (C_low, C_high, I_low, I_high)
    BREAKPOINTS: Dict[str, List[Tuple[float, float, float, float]]] = {
        "pm25": [
            (0.0, 30.0, 0.0, 50.0),
            (31.0, 60.0, 51.0, 100.0),
            (61.0, 90.0, 101.0, 200.0),
            (91.0, 120.0, 201.0, 300.0),
            (121.0, 250.0, 301.0, 400.0),
            (250.1, 500.0, 401.0, 500.0),
        ],
        "pm10": [
            (0.0, 50.0, 0.0, 50.0),
            (51.0, 100.0, 51.0, 100.0),
            (101.0, 250.0, 101.0, 200.0),
            (251.0, 350.0, 201.0, 300.0),
            (351.0, 430.0, 301.0, 400.0),
            (430.1, 600.0, 401.0, 500.0),
        ],
        "no2": [
            (0.0, 40.0, 0.0, 50.0),
            (41.0, 80.0, 51.0, 100.0),
            (81.0, 180.0, 101.0, 200.0),
            (181.0, 280.0, 201.0, 300.0),
            (281.0, 400.0, 301.0, 400.0),
            (400.1, 800.0, 401.0, 500.0),
        ],
        "o3": [
            (0.0, 50.0, 0.0, 50.0),
            (51.0, 100.0, 51.0, 100.0),
            (101.0, 168.0, 101.0, 200.0),
            (169.0, 208.0, 201.0, 300.0),
            (209.0, 748.0, 301.0, 400.0),
            (748.1, 1000.0, 401.0, 500.0),
        ],
        "so2": [
            (0.0, 40.0, 0.0, 50.0),
            (41.0, 80.0, 51.0, 100.0),
            (81.0, 380.0, 101.0, 200.0),
            (381.0, 800.0, 201.0, 300.0),
            (801.0, 1600.0, 301.0, 400.0),
            (1600.1, 2000.0, 401.0, 500.0),
        ],
        "co": [  # Note: CO is in mg/m³
            (0.0, 1.0, 0.0, 50.0),
            (1.1, 2.0, 51.0, 100.0),
            (2.1, 10.0, 101.0, 200.0),
            (10.1, 17.0, 201.0, 300.0),
            (17.1, 34.0, 301.0, 400.0),
            (34.1, 50.0, 401.0, 500.0),
        ],
    }

    CATEGORIES = [
        (0.0, 50.0, "Good", "#22C55E", "Minimal health impact"),
        (51.0, 100.0, "Satisfactory", "#84CC16", "Minor breathing discomfort to sensitive people"),
        (101.0, 200.0, "Moderate", "#EAB308", "Breathing discomfort to patients with asthma/heart disease"),
        (201.0, 300.0, "Poor", "#F97316", "Breathing discomfort to most people on prolonged exposure"),
        (301.0, 400.0, "Very Poor", "#EF4444", "Respiratory illness on prolonged exposure"),
        (401.0, 500.0, "Severe", "#7F1D1D", "Severe health impacts on healthy people and serious risks to vulnerable"),
    ]

    @classmethod
    def calculate_sub_index(cls, pollutant: str, concentration: Optional[float]) -> Optional[float]:
        """
        Calculates individual CPCB sub-index for a specific pollutant concentration
        using piecewise linear interpolation. Returns None if value is missing/invalid.
        """
        if concentration is None or np.isnan(concentration) or concentration < 0:
            return None

        poll = pollutant.lower()
        if poll not in cls.BREAKPOINTS:
            return None

        breakpoints = cls.BREAKPOINTS[poll]

        # Check below lowest
        if concentration < breakpoints[0][0]:
            return 0.0

        for c_low, c_high, i_low, i_high in breakpoints:
            if c_low <= concentration <= c_high:
                sub_index = i_low + ((i_high - i_low) / (c_high - c_low)) * (concentration - c_low)
                return round(float(sub_index), 1)

        # Above highest breakpoint: cap at 500 (Severe max)
        if concentration > breakpoints[-1][1]:
            return 500.0

        return None

    @classmethod
    def get_category_and_health_impact(cls, aqi: Optional[float]) -> Dict[str, str]:
        """
        Maps numerical AQI to CPCB category, color code, and health advisory.
        """
        if aqi is None or np.isnan(aqi):
            return {
                "category": "Unavailable",
                "color": "#94A3B8",
                "health_impact": "Insufficient data to determine official AQI.",
            }

        val = float(aqi)
        for low, high, name, color, impact in cls.CATEGORIES:
            if low <= val <= high or (name == "Severe" and val >= low):
                return {
                    "category": name,
                    "color": color,
                    "health_impact": impact,
                }

        return {
            "category": "Severe" if val > 500 else "Unknown",
            "color": "#7F1D1D" if val > 500 else "#94A3B8",
            "health_impact": "Hazardous emergency condition" if val > 500 else "Unknown",
        }

    @classmethod
    def compute_official_aqi(cls, pollutant_concentrations: Dict[str, Optional[float]]) -> Dict[str, Any]:
        """
        Computes statutory CPCB NAQI following strict official aggregation rules:
        1. Calculates sub-index for each valid pollutant.
        2. Requires at least 3 valid pollutants.
        3. Requires at least one particulate parameter (PM2.5 or PM10).
        4. Overall AQI = MAX(sub_indices). Prominent pollutant = argmax(sub_indices).
        """
        sub_indices: Dict[str, float] = {}
        for poll, conc in pollutant_concentrations.items():
            idx = cls.calculate_sub_index(poll, conc)
            if idx is not None:
                sub_indices[poll.lower()] = idx

        # Data sufficiency check
        has_particulate = ("pm25" in sub_indices) or ("pm10" in sub_indices)
        valid_count = len(sub_indices)

        if valid_count < 3 or not has_particulate:
            # Official AQI is unavailable according to CPCB rules
            reason = []
            if valid_count < 3:
                reason.append(f"Only {valid_count} valid pollutants available (CPCB requires minimum 3).")
            if not has_particulate:
                reason.append("Neither PM2.5 nor PM10 particulate parameters are available.")

            # Return partial diagnostic with individual sub-indices clearly labeled
            single_poll = "pm25" if "pm25" in sub_indices else ("pm10" if "pm10" in sub_indices else None)
            proxy_val = sub_indices.get(single_poll) if single_poll else None

            cat_info = cls.get_category_and_health_impact(proxy_val)

            return {
                "aqi": None,
                "is_official": False,
                "status": "insufficient_pollutants",
                "prominent_pollutant": None,
                "sub_indices": sub_indices,
                "category": f"Indicative ({cat_info['category']})" if proxy_val else "Unavailable",
                "indicative_sub_index": proxy_val,
                "color": cat_info["color"],
                "health_impact": f"{cat_info['health_impact']} (Note: Official AQI unavailable: {' '.join(reason)})",
                "rules_violation_reason": " ".join(reason),
            }

        # Statutory Max Sub-Index Rule
        prominent_poll = max(sub_indices, key=sub_indices.get)
        overall_aqi = round(sub_indices[prominent_poll], 1)
        cat_info = cls.get_category_and_health_impact(overall_aqi)

        return {
            "aqi": overall_aqi,
            "is_official": True,
            "status": "valid",
            "prominent_pollutant": prominent_poll.upper(),
            "sub_indices": sub_indices,
            "category": cat_info["category"],
            "color": cat_info["color"],
            "health_impact": cat_info["health_impact"],
            "rules_violation_reason": None,
        }
