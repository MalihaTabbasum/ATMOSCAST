"""
Plotly Visualization Suite for Model Explainability & SHAP (Phase 7).

Generates interactive charts with AtmosCast Deep Navy and Teal styling:
1. Global feature importance (mean absolute SHAP)
2. Feature group macro attribution (Pollution vs. Weather vs. Stability vs. Temporal)
3. Individual prediction waterfall decomposition
4. Meteorological non-linear SHAP dependence
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go

THEME = {
    "bg_color": "#0F172A",          # Deep Slate Navy
    "card_bg": "#1E293B",           # Dark Teal Navy Card
    "text_color": "#F8FAFC",        # Light neutral
    "muted_text": "#94A3B8",        # Slate
    "grid_color": "#334155",        # Muted gridline
    "teal": "#0D9488",              # Primary Teal
    "light_teal": "#14B8A6",        # Accent Cyan/Teal
    "coral": "#F43F5E",             # Severe/Positive push
    "amber": "#F59E0B",             # Caution
    "blue": "#38BDF8",              # Sky blue
}

GROUP_COLORS = {
    "Pollution History": THEME["coral"],
    "Surface Meteorology": THEME["blue"],
    "Atmospheric Stability & Inversion Proxies": THEME["amber"],
    "Temporal & Diurnal Cycles": THEME["light_teal"],
    "Other / Unclassified": THEME["muted_text"],
}


def apply_theme(fig: go.Figure, title: str, height: int = 500) -> go.Figure:
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>",
            "y": 0.95,
            "x": 0.05,
            "xanchor": "left",
            "yanchor": "top",
            "font": {"size": 17, "color": THEME["text_color"], "family": "Inter, Segoe UI, sans-serif"},
        },
        paper_bgcolor=THEME["bg_color"],
        plot_bgcolor=THEME["card_bg"],
        font={"color": THEME["text_color"], "family": "Inter, Segoe UI, sans-serif"},
        margin=dict(l=60, r=40, t=70, b=60),
        legend=dict(
            bgcolor="rgba(30, 41, 59, 0.8)",
            bordercolor=THEME["grid_color"],
            borderwidth=1,
            font=dict(color=THEME["text_color"], size=11),
        ),
        height=height,
    )
    fig.update_xaxes(
        gridcolor=THEME["grid_color"],
        zerolinecolor=THEME["grid_color"],
        tickfont=dict(color=THEME["muted_text"]),
        title_font=dict(color=THEME["text_color"]),
    )
    fig.update_yaxes(
        gridcolor=THEME["grid_color"],
        zerolinecolor=THEME["grid_color"],
        tickfont=dict(color=THEME["muted_text"]),
        title_font=dict(color=THEME["text_color"]),
    )
    return fig


def plot_global_shap_importance(
    importance_df: pd.DataFrame,
    horizon: int = 48,
    model_name: str = "XGBoost",
) -> go.Figure:
    """
    Horizontal bar chart of top features ranked by mean absolute SHAP value.
    """
    df = importance_df.sort_values(by="mean_abs_shap", ascending=True).reset_index(drop=True)
    fig = go.Figure()

    colors = [GROUP_COLORS.get(grp, THEME["teal"]) for grp in df["group"]]

    fig.add_trace(go.Bar(
        y=df["feature"],
        x=df["mean_abs_shap"],
        orientation="h",
        marker=dict(color=colors, line=dict(color=THEME["bg_color"], width=1)),
        hovertemplate="Feature: <b>%{y}</b><br>Mean |SHAP| Impact: %{x:.3f} µg/m³<extra></extra>",
    ))

    fig.update_xaxes(title="Mean Absolute SHAP Value (|Impact| on PM2.5 Forecast in µg/m³)")
    fig.update_yaxes(title="Feature Name")

    return apply_theme(fig, f"Global Feature Importance — {horizon}h Forecast ({model_name})", height=520)


def plot_feature_group_importance(
    group_df: pd.DataFrame,
    horizon: int = 48,
) -> go.Figure:
    """
    Donut chart of macro feature group percentage contributions.
    """
    colors = [GROUP_COLORS.get(grp, THEME["teal"]) for grp in group_df["group"]]

    fig = go.Figure(data=[go.Pie(
        labels=group_df["group"],
        values=group_df["percentage"],
        hole=0.55,
        marker=dict(colors=colors, line=dict(color=THEME["bg_color"], width=2)),
        textinfo="label+percent",
        textfont=dict(size=12, color=THEME["text_color"]),
        hovertemplate="Group: <b>%{label}</b><br>Share: %{percent}<extra></extra>",
    )])

    return apply_theme(fig, f"Macro Feature Group Contribution Share — {horizon}h Horizon", height=480)


def plot_waterfall_explanation(
    explanation: Dict[str, Any],
    sample_title: str = "January 5, 2024 (Severe Smog Episode Prediction)",
) -> go.Figure:
    """
    Interactive waterfall chart decomposing base value -> feature shifts -> final forecast.
    """
    base_val = explanation["base_value"]
    top_contribs = explanation["top_contributions"]
    pred_val = explanation["prediction"]

    measures = ["absolute"]
    x_labels = ["Baseline E[f(X)]"]
    y_vals = [base_val]
    text_labels = [f"{base_val:.1f}"]

    for item in top_contribs:
        feat = item["feature"]
        val = item["value"]
        shap_val = item["shap_value"]
        measures.append("relative")
        x_labels.append(f"{feat}<br>({val:.1f})")
        y_vals.append(shap_val)
        text_labels.append(f"{'+' if shap_val > 0 else ''}{shap_val:.1f}")

    # Final prediction bar
    measures.append("total")
    x_labels.append("Final Forecast")
    y_vals.append(pred_val)
    text_labels.append(f"{pred_val:.1f}")

    fig = go.Figure(go.Waterfall(
        name="SHAP Attribution",
        orientation="v",
        measure=measures,
        x=x_labels,
        textposition="outside",
        text=text_labels,
        y=y_vals,
        connector={"line": {"color": THEME["grid_color"]}},
        decreasing={"marker": {"color": THEME["light_teal"]}},
        increasing={"marker": {"color": THEME["coral"]}},
        totals={"marker": {"color": THEME["amber"]}},
    ))

    fig.update_yaxes(title="Predicted PM2.5 Concentration (µg/m³)")

    return apply_theme(fig, f"Local SHAP Waterfall Decomposition — {sample_title}", height=520)


def plot_shap_dependence(
    feature_vals: np.ndarray,
    shap_vals: np.ndarray,
    feature_name: str = "wind_speed_10m",
    display_title: str = "10m Surface Wind Speed",
    unit: str = "km/h",
) -> go.Figure:
    """
    Scatter plot of feature value vs. SHAP attribution value.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=feature_vals,
        y=shap_vals,
        mode="markers",
        marker=dict(
            color=THEME["light_teal"],
            size=7,
            opacity=0.7,
            line=dict(color=THEME["bg_color"], width=1),
        ),
        hovertemplate=f"{display_title}: %{{x:.1f}} {unit}<br>SHAP Impact: %{{y:.2f}} µg/m³<extra></extra>",
    ))

    fig.add_hline(y=0, line_dash="dash", line_color=THEME["coral"])

    fig.update_xaxes(title=f"{display_title} ({unit})")
    fig.update_yaxes(title="SHAP Impact on PM2.5 Forecast (µg/m³)")

    return apply_theme(fig, f"Atmospheric Sensitivity: {display_title} vs. SHAP Attribution")
