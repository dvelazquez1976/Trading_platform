"""Utilidades de tema y componentes visuales reutilizables."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "config.json"

_DARK_CSS = """
<style>
/* ── Fondos principales ── */
.stApp                               { background-color: #0f172a !important; color: #e2e8f0 !important; }
[data-testid="stSidebar"]            { background-color: #1e293b !important; }
[data-testid="stHeader"]             { background-color: #0f172a !important; border-bottom: 1px solid #334155 !important; }
section[data-testid="stSidebar"] > div { background-color: #1e293b !important; }

/* ── Contenedores y tarjetas ── */
[data-testid="stVerticalBlockBorderWrapper"] > div { background-color: #1e293b !important; border-color: #334155 !important; }
div[data-testid="stExpander"]        { background-color: #1e293b !important; border-color: #334155 !important; }

/* ── Métricas ── */
[data-testid="metric-container"]     { background-color: #1e293b !important; border-radius: 8px; padding: 8px; }
[data-testid="stMetricValue"]        { color: #f1f5f9 !important; }
[data-testid="stMetricLabel"]        { color: #94a3b8 !important; }
[data-testid="stMetricDelta"]        { color: #94a3b8 !important; }

/* ── Texto ── */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 { color: #e2e8f0 !important; }
label[data-testid="stWidgetLabel"]   { color: #cbd5e1 !important; }
.stCaption                           { color: #64748b !important; }

/* ── Inputs y controles ── */
.stTextInput > div > div            { background-color: #1e293b !important; border-color: #334155 !important; color: #e2e8f0 !important; }
.stSelectbox > div > div            { background-color: #1e293b !important; border-color: #334155 !important; color: #e2e8f0 !important; }
.stMultiSelect > div > div          { background-color: #1e293b !important; border-color: #334155 !important; }
.stNumberInput > div > div          { background-color: #1e293b !important; border-color: #334155 !important; }
.stSlider > div                     { color: #e2e8f0 !important; }

/* ── Tablas/dataframes ── */
[data-testid="stDataFrame"]          { background-color: #1e293b !important; }
thead tr th                          { background-color: #0f172a !important; color: #94a3b8 !important; }
tbody tr td                          { background-color: #1e293b !important; color: #e2e8f0 !important; }
tbody tr:hover td                    { background-color: #334155 !important; }

/* ── Alertas/info boxes ── */
[data-testid="stAlert"]             { background-color: #1e293b !important; border-color: #334155 !important; }

/* ── Tabs ── */
[data-testid="stTabs"]              { background-color: #0f172a !important; }
button[data-testid="stTab"]         { color: #94a3b8 !important; }
button[data-testid="stTab"][aria-selected="true"] { color: #3b82f6 !important; border-bottom-color: #3b82f6 !important; }

/* ── Divider ── */
hr { border-color: #334155 !important; }
</style>
"""

_LIGHT_CSS = ""


def _load_theme() -> str:
    try:
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg.get("ui", {}).get("theme", "light")
    except Exception:
        return "light"


def apply_theme() -> str:
    """Inyecta CSS de tema y devuelve el nombre del tema activo ('light'/'dark')."""
    theme = _load_theme()
    if theme == "dark":
        st.markdown(_DARK_CSS, unsafe_allow_html=True)
    return theme


def sparkline(
    series: pd.Series,
    color: str | None = None,
    height: int = 60,
    show_area: bool = True,
) -> go.Figure:
    """Gráfico de línea minimalista para incrustar en tarjetas."""
    if color is None:
        pct = (series.iloc[-1] - series.iloc[0]) / (series.iloc[0] + 1e-9)
        color = "#16a34a" if pct >= 0 else "#dc2626"

    fill = "tozeroy" if show_area else "none"
    fill_color = color.replace(")", ", 0.12)").replace("rgb(", "rgba(") if show_area else "rgba(0,0,0,0)"
    if fill_color == color:
        fill_color = color + "20"

    fig = go.Figure(
        go.Scatter(
            y=series.values,
            mode="lines",
            line=dict(color=color, width=1.5),
            fill=fill,
            fillcolor=fill_color,
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True),
    )
    return fig


def export_csv_es(df: pd.DataFrame) -> bytes:
    """CSV con separador ';' y decimal ',' (formato español/europeo)."""
    return df.to_csv(sep=";", decimal=",", index=False).encode("utf-8-sig")
