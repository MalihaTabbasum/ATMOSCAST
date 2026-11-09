"""
Plotly Visualization Suite for Model Evaluation and Diagnostics (Phase 6).

Generates interactive charts with AtmosCast Deep Navy and Teal styling:
1. Actual vs. Predicted scatter & time-series overlay
2. Residual diagnostics (histogram & residuals vs. predicted)
3. Multi-model & multi-tier comparison bar charts
4. Horizon-wise error growth trajectories (24h to 72h)
5. Atmospheric regime performance breakdown
6. Severe pollution episode error analysis
"""

from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

THEME = {
    "bg_color": "#0F172A",          # Deep Slate Navy
    "card_bg": "#1E293B",           # Dark Teal Navy Card
    "text_color": "#F8FAFC",        # Light neutral
    "muted_text": "#94A3B8",        # Slate
    "grid_color": "#334155",        # Muted gridline
    "teal": "#0D9488",              # Primary Teal
    "light_teal": "#14B8A6",        # Accent Cyan/Teal
    "coral": "#F43F5E",             # Severe/Alert
    "amber": "#F59E0B",             # Caution
    "blue": "#38BDF8",              # Sky blue
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


def plot_actual_vs_predicted(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    horizon: int = 24,
    model_name: str = "XGBoost",
) -> go.Figure:
    """
    Scatter plot with 1:1 perfect prediction line and error bands.
    """
    fig = go.Figure()

    # Scatter points
    fig.add_trace(go.Scatter(
        x=y_true,
        y=y_pred,
        mode="markers",
        name="Observations",
        marker=dict(
            color=THEME["light_teal"],
            size=7,
            opacity=0.75,
            line=dict(width=1, color=THEME["bg_color"]),
        ),
        hovertemplate="Actual: %{x:.1f} µg/m³<br>Predicted: %{y:.1f} µg/m³<extra></extra>",
    ))

    # 1:1 Reference Line
    min_val = min(float(np.min(y_true)), float(np.min(y_pred))) * 0.9
    max_val = max(float(np.max(y_true)), float(np.max(y_pred))) * 1.05

    fig.add_trace(go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode="lines",
        name="Ideal 1:1 Line",
        line=dict(color=THEME["coral"], dash="dash", width=2),
    ))

    fig.update_xaxes(title="Actual PM2.5 (µg/m³)")
    fig.update_yaxes(title="Predicted PM2.5 (µg/m³)")

    return apply_theme(fig, f"Actual vs. Predicted PM2.5 — {horizon}h Horizon ({model_name})")


def plot_residuals_diagnostic(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    horizon: int = 24,
    model_name: str = "XGBoost",
) -> go.Figure:
    """
    Dual-panel residual diagnostic: Residual distribution and Residuals vs. Predicted.
    """
    residuals = y_pred - y_true
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Residual Distribution Histogram", "Residuals vs. Predicted (Heteroscedasticity Check)"),
        horizontal_spacing=0.12,
    )

    # Histogram
    fig.add_trace(go.Histogram(
        x=residuals,
        nbinsx=25,
        name="Residuals",
        marker_color=THEME["blue"],
        opacity=0.8,
        hovertemplate="Error Bin: %{x:.1f}<br>Count: %{y}<extra></extra>",
    ), row=1, col=1)

    # Zero error vertical line on histogram
    fig.add_vline(x=0, line_dash="dash", line_color=THEME["coral"], row=1, col=1)

    # Residuals vs Predicted
    fig.add_trace(go.Scatter(
        x=y_pred,
        y=residuals,
        mode="markers",
        name="Residual vs Pred",
        marker=dict(color=THEME["light_teal"], size=6, opacity=0.7),
        hovertemplate="Predicted: %{x:.1f}<br>Residual: %{y:.1f}<extra></extra>",
    ), row=1, col=2)

    # Zero error horizontal line on scatter
    fig.add_hline(y=0, line_dash="dash", line_color=THEME["coral"], row=1, col=2)

    fig.update_xaxes(title_text="Residual Error (µg/m³)", row=1, col=1)
    fig.update_yaxes(title_text="Frequency", row=1, col=1)
    fig.update_xaxes(title_text="Predicted PM2.5 (µg/m³)", row=1, col=2)
    fig.update_yaxes(title_text="Residual Error (µg/m³)", row=1, col=2)

    return apply_theme(fig, f"Residual Diagnostics & Bias Analysis — {horizon}h ({model_name})", height=480)


def plot_model_comparison_bars(eval_df: pd.DataFrame) -> go.Figure:
    """
    Grouped bar charts comparing Validation & Test RMSE across all models and tiers.
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Validation RMSE by Model & Tier (Selection Criterion)", "Held-Out Test RMSE Comparison"),
        horizontal_spacing=0.10,
    )

    horizons = sorted(eval_df["horizon"].unique())

    colors = {
        "persistence": THEME["muted_text"],
        "random_forest": THEME["amber"],
        "xgboost": THEME["teal"],
    }

    # Group summary
    for m_type in ["persistence", "random_forest", "xgboost"]:
        sub = eval_df[eval_df["model_type"] == m_type].groupby("horizon").agg({"val_rmse": "mean", "test_rmse": "mean"}).reset_index()

        # Validation Bar
        fig.add_trace(go.Bar(
            x=[f"{h}h" for h in sub["horizon"]],
            y=sub["val_rmse"],
            name=f"{m_type.title()} (Val)",
            marker_color=colors[m_type],
            hovertemplate="Horizon: %{x}<br>Val RMSE: %{y:.2f} µg/m³<extra></extra>",
        ), row=1, col=1)

        # Test Bar
        fig.add_trace(go.Bar(
            x=[f"{h}h" for h in sub["horizon"]],
            y=sub["test_rmse"],
            name=f"{m_type.title()} (Test)",
            marker_color=colors[m_type],
            opacity=0.75,
            hovertemplate="Horizon: %{x}<br>Test RMSE: %{y:.2f} µg/m³<extra></extra>",
        ), row=1, col=2)

    fig.update_yaxes(title_text="RMSE (µg/m³)", row=1, col=1)
    fig.update_yaxes(title_text="RMSE (µg/m³)", row=1, col=2)

    return apply_theme(fig, "Multi-Model Forecast Error Benchmark across Horizons", height=500)


def plot_horizon_error_trajectory(best_models_df: pd.DataFrame) -> go.Figure:
    """
    Line chart displaying error progression (RMSE and MAE) from 24h to 48h to 72h.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=[f"{int(h)}h" for h in best_models_df["horizon"]],
        y=best_models_df["val_rmse"],
        mode="lines+markers",
        name="Validation RMSE",
        line=dict(color=THEME["light_teal"], width=3),
        marker=dict(size=9),
    ))

    fig.add_trace(go.Scatter(
        x=[f"{int(h)}h" for h in best_models_df["horizon"]],
        y=best_models_df["val_mae"],
        mode="lines+markers",
        name="Validation MAE",
        line=dict(color=THEME["blue"], width=2, dash="dot"),
        marker=dict(size=8),
    ))

    fig.add_trace(go.Scatter(
        x=[f"{int(h)}h" for h in best_models_df["horizon"]],
        y=best_models_df["test_rmse"],
        mode="lines+markers",
        name="Test RMSE",
        line=dict(color=THEME["coral"], width=3),
        marker=dict(size=9),
    ))

    fig.add_trace(go.Scatter(
        x=[f"{int(h)}h" for h in best_models_df["horizon"]],
        y=best_models_df["test_mae"],
        mode="lines+markers",
        name="Test MAE",
        line=dict(color=THEME["amber"], width=2, dash="dot"),
        marker=dict(size=8),
    ))

    fig.update_xaxes(title="Forecast Lookahead Horizon")
    fig.update_yaxes(title="Error (µg/m³)")

    return apply_theme(fig, "Forecast Error Growth Trajectory (24h to 72h Horizons)")


def plot_regime_performance(regime_df: pd.DataFrame) -> go.Figure:
    """
    Bar chart showing performance breakdown across atmospheric stability regimes.
    """
    fig = go.Figure()

    regimes = regime_df["regime"].unique()
    colors = [THEME["coral"], THEME["light_teal"], THEME["amber"]]

    for i, reg in enumerate(regimes):
        sub = regime_df[regime_df["regime"] == reg]
        fig.add_trace(go.Bar(
            x=sub["horizon"],
            y=sub["rmse"],
            name=reg,
            marker_color=colors[i % len(colors)],
            hovertemplate="Horizon: %{x}<br>RMSE: %{y:.2f} µg/m³<extra></extra>",
        ))

    fig.update_xaxes(title="Forecast Horizon")
    fig.update_yaxes(title="RMSE (µg/m³)")

    return apply_theme(fig, "Atmospheric Regime Stratification: Nocturnal Stagnant vs. Convective Daytime")


def plot_severe_episode_errors(episode_df: pd.DataFrame) -> go.Figure:
    """
    Bar chart illustrating error inflation and systematic underprediction (MBE) during severe episodes.
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("RMSE: Severe Episodes vs. Moderate Conditions", "Mean Bias Error (MBE): Peak Underprediction"),
        horizontal_spacing=0.12,
    )

    regimes = episode_df["regime"].unique()
    colors = {"Severe Episode (>= 120 µg/m³)": THEME["coral"], "Moderate / Standard (< 120 µg/m³)": THEME["light_teal"]}

    for reg in regimes:
        sub = episode_df[episode_df["regime"] == reg]
        fig.add_trace(go.Bar(
            x=sub["horizon"],
            y=sub["rmse"],
            name=f"{reg} (RMSE)",
            marker_color=colors.get(reg, THEME["blue"]),
            hovertemplate="Horizon: %{x}<br>RMSE: %{y:.2f} µg/m³<extra></extra>",
        ), row=1, col=1)

        fig.add_trace(go.Bar(
            x=sub["horizon"],
            y=sub["mbe"],
            name=f"{reg} (MBE)",
            marker_color=colors.get(reg, THEME["blue"]),
            opacity=0.75,
            hovertemplate="Horizon: %{x}<br>MBE: %{y:.2f} µg/m³<extra></extra>",
        ), row=1, col=2)

    fig.add_hline(y=0, line_dash="dash", line_color=THEME["text_color"], row=1, col=2)

    fig.update_yaxes(title_text="RMSE (µg/m³)", row=1, col=1)
    fig.update_yaxes(title_text="Mean Bias Error (µg/m³)", row=1, col=2)

    return apply_theme(fig, "Severe Pollution Episode Performance & Systematic Bias Analysis", height=500)
