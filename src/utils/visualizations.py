"""
AtmosCast Visualization Utilities
Provides interactive Plotly charts for exploratory data analysis, atmospheric correlation,
diurnal cycle tracking, station comparisons, and pollution episode diagnostics.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Master UI Design Tokens
COLORS = {
    "navy": "#0F172A",
    "teal": "#0D9488",
    "teal_light": "#14B8A6",
    "coral": "#EF4444",
    "amber": "#F59E0B",
    "blue": "#3B82F6",
    "purple": "#8B5CF6",
    "slate": "#64748B",
    "bg_light": "#F8FAFC",
    "grid_gray": "#E2E8F0",
}

STATION_PALETTE = {
    "delhi_anand_vihar": "#EF4444",      # High hotspot red
    "delhi_punjabi_bagh": "#F97316",     # Orange
    "delhi_rk_puram": "#0D9488",         # Teal
    "noida_sector_62": "#3B82F6",        # Blue
    "gurugram_vikas_sadan": "#8B5CF6",   # Purple
    "delhi_igi_airport": "#10B981",      # Emerald
}


def _apply_clean_layout(fig: go.Figure, title: str, x_title: str = "", y_title: str = "") -> go.Figure:
    """Apply consistent modern typography, neutral background, and subtle grids to Plotly figure."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>",
            "x": 0.02,
            "xanchor": "left",
            "font": {"size": 17, "family": "Arial, sans-serif", "color": COLORS["navy"]},
        },
        font={"family": "Arial, sans-serif", "color": COLORS["navy"]},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        margin={"l": 60, "r": 40, "t": 60, "b": 50},
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
            "bgcolor": "rgba(255, 255, 255, 0.8)",
        },
    )
    if x_title:
        fig.update_xaxes(title_text=x_title, showgrid=True, gridcolor=COLORS["grid_gray"], zeroline=False)
    else:
        fig.update_xaxes(showgrid=True, gridcolor=COLORS["grid_gray"], zeroline=False)

    if y_title:
        fig.update_yaxes(title_text=y_title, showgrid=True, gridcolor=COLORS["grid_gray"], zeroline=False)
    else:
        fig.update_yaxes(showgrid=True, gridcolor=COLORS["grid_gray"], zeroline=False)

    return fig


def plot_pm25_timeseries(df: pd.DataFrame) -> go.Figure:
    """Plot hourly PM2.5 time series across stations with WHO & CPCB reference lines."""
    fig = go.Figure()

    for station_id, group in df.groupby("station_id"):
        st_name = group["station_name"].iloc[0]
        color = STATION_PALETTE.get(station_id, COLORS["teal"])
        fig.add_trace(go.Scatter(
            x=group["timestamp_utc"],
            y=group["pm25"],
            mode="lines",
            name=st_name,
            line={"width": 2, "color": color},
            hovertemplate="%{y:.1f} µg/m³",
        ))

    # CPCB 24-hr Standard Line (60 µg/m³)
    fig.add_hline(
        y=60.0,
        line_dash="dash",
        line_color=COLORS["amber"],
        line_width=1.8,
        annotation_text="CPCB 24h Standard (60 µg/m³)",
        annotation_position="top left",
        annotation_font_color=COLORS["amber"],
    )

    # WHO 24-hr Guideline Line (15 µg/m³)
    fig.add_hline(
        y=15.0,
        line_dash="dot",
        line_color=COLORS["coral"],
        line_width=1.5,
        annotation_text="WHO 24h Guideline (15 µg/m³)",
        annotation_position="bottom left",
        annotation_font_color=COLORS["coral"],
    )

    _apply_clean_layout(
        fig,
        title="Hourly PM2.5 Particulate Matter Trajectories across Delhi NCR CAAQMS Stations",
        x_title="Date & Time (UTC)",
        y_title="PM2.5 Concentration (µg/m³)",
    )
    return fig


def plot_pm10_timeseries(df: pd.DataFrame) -> go.Figure:
    """Plot hourly PM10 coarse particulate time series with CPCB statutory limit."""
    fig = go.Figure()

    for station_id, group in df.groupby("station_id"):
        st_name = group["station_name"].iloc[0]
        color = STATION_PALETTE.get(station_id, COLORS["blue"])
        fig.add_trace(go.Scatter(
            x=group["timestamp_utc"],
            y=group["pm10"],
            mode="lines",
            name=st_name,
            line={"width": 2, "color": color},
            hovertemplate="%{y:.1f} µg/m³",
        ))

    # CPCB 24-hr PM10 Standard (100 µg/m³)
    fig.add_hline(
        y=100.0,
        line_dash="dash",
        line_color=COLORS["amber"],
        line_width=1.8,
        annotation_text="CPCB 24h Standard (100 µg/m³)",
        annotation_position="top left",
        annotation_font_color=COLORS["amber"],
    )

    _apply_clean_layout(
        fig,
        title="Hourly PM10 Coarse Particulate Matter Trajectories across Delhi NCR",
        x_title="Date & Time (UTC)",
        y_title="PM10 Concentration (µg/m³)",
    )
    return fig


def plot_diurnal_cycles(df: pd.DataFrame) -> go.Figure:
    """Plot mean diurnal cycle across hour of day (IST) comparing PM2.5, PM10, NO2, and Ozone."""
    diurnal = df.groupby("hour_ist")[["pm25", "pm10", "no2", "o3"]].mean().reset_index()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # PM2.5 & PM10 (Left Y-axis)
    fig.add_trace(
        go.Scatter(
            x=diurnal["hour_ist"],
            y=diurnal["pm25"],
            name="PM2.5",
            mode="lines+markers",
            line={"color": COLORS["coral"], "width": 3},
            marker={"size": 6},
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=diurnal["hour_ist"],
            y=diurnal["pm10"],
            name="PM10",
            mode="lines+markers",
            line={"color": COLORS["amber"], "width": 2.5, "dash": "dash"},
            marker={"size": 6},
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=diurnal["hour_ist"],
            y=diurnal["no2"],
            name="NO2",
            mode="lines+markers",
            line={"color": COLORS["purple"], "width": 2},
            marker={"size": 5},
        ),
        secondary_y=False,
    )

    # Ozone (Right Y-axis - Photochemical afternoon peak)
    fig.add_trace(
        go.Scatter(
            x=diurnal["hour_ist"],
            y=diurnal["o3"],
            name="Ground Ozone (O3)",
            mode="lines+markers",
            line={"color": COLORS["teal"], "width": 3},
            marker={"size": 7, "symbol": "diamond"},
        ),
        secondary_y=True,
    )

    fig.update_xaxes(
        title_text="Hour of Day (IST — Asia/Kolkata)",
        tickmode="linear",
        tick0=0,
        dtick=2,
        showgrid=True,
        gridcolor=COLORS["grid_gray"],
    )
    fig.update_yaxes(title_text="Particulates & NO2 (µg/m³)", secondary_y=False, showgrid=True, gridcolor=COLORS["grid_gray"])
    fig.update_yaxes(title_text="Ozone O3 (µg/m³)", secondary_y=True, showgrid=False)

    _apply_clean_layout(
        fig,
        title="Diurnal Cycle Dynamics: Nocturnal Boundary Compression vs. Afternoon Ozone Formation",
    )
    return fig


def plot_daily_trend_comparison(df: pd.DataFrame) -> go.Figure:
    """Plot daily progression of median and IQR particulate levels across Delhi NCR."""
    df_plot = df.copy()
    daily_stats = df_plot.groupby("date_ist")["pm25"].agg([
        ("median", "median"),
        ("q25", lambda x: x.quantile(0.25)),
        ("q75", lambda x: x.quantile(0.75)),
        ("min", "min"),
        ("max", "max"),
    ]).reset_index()

    fig = go.Figure()

    # Interquartile shading
    fig.add_trace(go.Scatter(
        x=list(daily_stats["date_ist"]) + list(daily_stats["date_ist"])[::-1],
        y=list(daily_stats["q75"]) + list(daily_stats["q25"])[::-1],
        fill="toself",
        fillcolor="rgba(13, 148, 136, 0.2)",
        line={"color": "rgba(255,255,255,0)"},
        name="IQR (25th–75th Percentile)",
        hoverinfo="skip",
    ))

    # Median line
    fig.add_trace(go.Scatter(
        x=daily_stats["date_ist"],
        y=daily_stats["median"],
        mode="lines+markers",
        name="Median PM2.5",
        line={"color": COLORS["teal"], "width": 3},
        marker={"size": 8},
        hovertemplate="Date: %{x}<br>Median PM2.5: %{y:.1f} µg/m³",
    ))

    # Min/Max range
    fig.add_trace(go.Scatter(
        x=daily_stats["date_ist"],
        y=daily_stats["max"],
        mode="markers",
        name="Max PM2.5 Peak",
        marker={"color": COLORS["coral"], "size": 9, "symbol": "triangle-up"},
        hovertemplate="Max: %{y:.1f} µg/m³",
    ))

    _apply_clean_layout(
        fig,
        title="Daily Regional PM2.5 Trends & Airshed Range (January 1–7, 2024)",
        x_title="Date (IST)",
        y_title="PM2.5 (µg/m³)",
    )
    return fig


def plot_station_comparison(df: pd.DataFrame) -> go.Figure:
    """Plot station-wise distribution comparison boxplots for PM2.5."""
    fig = px.box(
        df,
        x="station_name",
        y="pm25",
        color="station_name",
        points="outliers",
        color_discrete_sequence=[STATION_PALETTE.get(sid, COLORS["teal"]) for sid in df["station_id"].unique()],
    )

    fig.add_hline(
        y=60.0,
        line_dash="dash",
        line_color=COLORS["amber"],
        annotation_text="CPCB 24h Standard (60 µg/m³)",
        annotation_position="top left",
    )

    _apply_clean_layout(
        fig,
        title="Station-to-Station PM2.5 Distribution & Spatial Variability",
        x_title="Monitoring Station",
        y_title="PM2.5 Concentration (µg/m³)",
    )
    fig.update_layout(showlegend=False)
    return fig


def plot_correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    """Plot Pearson correlation matrix between pollutants and surface meteorological variables."""
    corr_cols = [
        "pm25", "pm10", "no2", "o3", "so2", "co",
        "temperature_2m", "relative_humidity_2m", "surface_pressure", "wind_speed_10m", "precipitation"
    ]
    avail_cols = [c for c in corr_cols if c in df.columns]
    corr_matrix = df[avail_cols].corr()

    # Clean display labels
    col_labels = {
        "pm25": "PM2.5",
        "pm10": "PM10",
        "no2": "NO2",
        "o3": "Ozone (O3)",
        "so2": "SO2",
        "co": "CO",
        "temperature_2m": "Temp (2m)",
        "relative_humidity_2m": "Humidity (RH)",
        "surface_pressure": "Pressure",
        "wind_speed_10m": "Wind Speed",
        "precipitation": "Rain",
    }
    display_names = [col_labels.get(c, c) for c in avail_cols]

    fig = px.imshow(
        corr_matrix.values,
        x=display_names,
        y=display_names,
        color_continuous_scale="RdBu_r",
        zmin=-1.0,
        zmax=1.0,
        text_auto=".2f",
        aspect="auto",
    )

    _apply_clean_layout(
        fig,
        title="Pearson Correlation Matrix: Air Pollutants vs. Boundary-Layer Meteorology",
    )
    fig.update_layout(
        coloraxis_colorbar={
            "title": "Pearson r",
            "tickvals": [-1.0, -0.5, 0.0, 0.5, 1.0],
        }
    )
    return fig


def plot_weather_relationships_grid(df: pd.DataFrame) -> go.Figure:
    """Plot 2x2 grid of key physical meteorological relationships with PM2.5."""
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "PM2.5 vs. Wind Speed (Stagnation Threshold < 5 km/h)",
            "PM2.5 vs. Temperature (Nocturnal Thermal Inversion)",
            "PM2.5 vs. Relative Humidity (Secondary Aerosol Trapping)",
            "PM2.5 vs. Surface Pressure (Anticyclonic Subsidence)",
        ),
        horizontal_spacing=0.1,
        vertical_spacing=0.15,
    )

    # 1. PM2.5 vs Wind Speed
    fig.add_trace(
        go.Scatter(
            x=df["wind_speed_10m"],
            y=df["pm25"],
            mode="markers",
            marker={"color": COLORS["teal"], "size": 5, "opacity": 0.6},
            name="Wind Speed",
            hovertemplate="Wind: %{x:.1f} km/h<br>PM2.5: %{y:.1f} µg/m³",
        ),
        row=1, col=1,
    )

    # 2. PM2.5 vs Temperature
    fig.add_trace(
        go.Scatter(
            x=df["temperature_2m"],
            y=df["pm25"],
            mode="markers",
            marker={"color": COLORS["coral"], "size": 5, "opacity": 0.6},
            name="Temperature",
            hovertemplate="Temp: %{x:.1f} °C<br>PM2.5: %{y:.1f} µg/m³",
        ),
        row=1, col=2,
    )

    # 3. PM2.5 vs Relative Humidity
    fig.add_trace(
        go.Scatter(
            x=df["relative_humidity_2m"],
            y=df["pm25"],
            mode="markers",
            marker={"color": COLORS["blue"], "size": 5, "opacity": 0.6},
            name="Humidity",
            hovertemplate="RH: %{x:.1f} %<br>PM2.5: %{y:.1f} µg/m³",
        ),
        row=2, col=1,
    )

    # 4. PM2.5 vs Surface Pressure
    fig.add_trace(
        go.Scatter(
            x=df["surface_pressure"],
            y=df["pm25"],
            mode="markers",
            marker={"color": COLORS["purple"], "size": 5, "opacity": 0.6},
            name="Pressure",
            hovertemplate="Pressure: %{x:.1f} hPa<br>PM2.5: %{y:.1f} µg/m³",
        ),
        row=2, col=2,
    )

    fig.update_xaxes(title_text="10m Wind Speed (km/h)", row=1, col=1, gridcolor=COLORS["grid_gray"])
    fig.update_xaxes(title_text="2m Temperature (°C)", row=1, col=2, gridcolor=COLORS["grid_gray"])
    fig.update_xaxes(title_text="Relative Humidity (%)", row=2, col=1, gridcolor=COLORS["grid_gray"])
    fig.update_xaxes(title_text="Surface Pressure (hPa)", row=2, col=2, gridcolor=COLORS["grid_gray"])

    fig.update_yaxes(title_text="PM2.5 (µg/m³)", row=1, col=1, gridcolor=COLORS["grid_gray"])
    fig.update_yaxes(title_text="PM2.5 (µg/m³)", row=1, col=2, gridcolor=COLORS["grid_gray"])
    fig.update_yaxes(title_text="PM2.5 (µg/m³)", row=2, col=1, gridcolor=COLORS["grid_gray"])
    fig.update_yaxes(title_text="PM2.5 (µg/m³)", row=2, col=2, gridcolor=COLORS["grid_gray"])

    _apply_clean_layout(
        fig,
        title="Physical Weather Drivers of Fine Particulate Accumulation",
    )
    fig.update_layout(showlegend=False, height=750)
    return fig


def plot_pollution_episode_deepdive(df: pd.DataFrame, station_id: str = "delhi_anand_vihar") -> go.Figure:
    """Plot synchronized 4-row multi-parameter diagnostic chart during the severe January 5–6 smog episode."""
    st_df = df[df["station_id"] == station_id].sort_values("timestamp_utc").copy()
    if st_df.empty:
        st_df = df.sort_values("timestamp_utc").copy()

    st_name = st_df["station_name"].iloc[0] if "station_name" in st_df.columns else station_id

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=(
            f"1. Particulate Mass Concentration ({st_name})",
            "2. Horizontal Ventilation (10m Wind Speed)",
            "3. Surface Boundary Thermal Inversion Proxy (2m Temperature)",
            "4. Atmospheric Moisture Saturation (Relative Humidity)",
        ),
    )

    # 1. PM2.5 & PM10
    fig.add_trace(
        go.Scatter(
            x=st_df["timestamp_utc"],
            y=st_df["pm25"],
            mode="lines",
            name="PM2.5",
            line={"color": COLORS["coral"], "width": 2.5},
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=st_df["timestamp_utc"],
            y=st_df["pm10"],
            mode="lines",
            name="PM10",
            line={"color": COLORS["amber"], "width": 1.8, "dash": "dot"},
        ),
        row=1, col=1,
    )

    # 2. Wind Speed
    fig.add_trace(
        go.Scatter(
            x=st_df["timestamp_utc"],
            y=st_df["wind_speed_10m"],
            mode="lines",
            name="Wind Speed",
            line={"color": COLORS["teal"], "width": 2},
        ),
        row=2, col=1,
    )
    # Stagnation line (5 km/h)
    fig.add_hline(y=5.0, line_dash="dash", line_color=COLORS["slate"], row=2, col=1)

    # 3. Temperature
    fig.add_trace(
        go.Scatter(
            x=st_df["timestamp_utc"],
            y=st_df["temperature_2m"],
            mode="lines",
            name="Temperature",
            line={"color": COLORS["blue"], "width": 2},
        ),
        row=3, col=1,
    )

    # 4. Humidity
    fig.add_trace(
        go.Scatter(
            x=st_df["timestamp_utc"],
            y=st_df["relative_humidity_2m"],
            mode="lines",
            name="Relative Humidity",
            line={"color": COLORS["purple"], "width": 2},
        ),
        row=4, col=1,
    )

    fig.update_yaxes(title_text="µg/m³", row=1, col=1, gridcolor=COLORS["grid_gray"])
    fig.update_yaxes(title_text="km/h", row=2, col=1, gridcolor=COLORS["grid_gray"])
    fig.update_yaxes(title_text="°C", row=3, col=1, gridcolor=COLORS["grid_gray"])
    fig.update_yaxes(title_text="%", row=4, col=1, gridcolor=COLORS["grid_gray"])
    fig.update_xaxes(title_text="Date & Time (UTC)", row=4, col=1, gridcolor=COLORS["grid_gray"])

    _apply_clean_layout(
        fig,
        title=f"Coupled Atmospheric Episode Diagnostic: Stagnation Breakdown at {st_name}",
    )
    fig.update_layout(height=850)
    return fig
