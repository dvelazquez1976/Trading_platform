"""Generación de gráficos Plotly interactivos."""

import os
from datetime import datetime, timedelta
from typing import Dict

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from trading_platform.core.constants import REPORTS_DIR
from trading_platform.core.logging import get_logger
from trading_platform.visualization.theme import get_theme

logger = get_logger(__name__)

CHART_HEIGHT   = 1000
MONTHS_DISPLAY = 24
ROW_CFG = {
    'price': 1, 'volume': 2, 'macd': 3, 'rsi': 4, 'willr': 5,
    'heights': [0.45, 0.1, 0.15, 0.15, 0.15], 'spacing': 0.03
}


def generar_grafico(datos: pd.DataFrame, resultado: Dict, ticker: str,
                    output_dir: str = None, theme_name: str = "light"):
    """Genera HTML con gráfico interactivo + tabla de señales."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = output_dir or str(REPORTS_DIR)
    os.makedirs(out, exist_ok=True)

    C = get_theme(theme_name)
    filtrado = _last_n_months(datos, MONTHS_DISPLAY)

    fig = make_subplots(
        rows=5, cols=1, shared_xaxes=True,
        vertical_spacing=ROW_CFG['spacing'],
        subplot_titles=(f'📈 {ticker} — Velas', '📊 Volumen', '📉 MACD', '🟣 RSI', '🌊 Williams %R'),
        row_heights=ROW_CFG['heights']
    )

    _add_candlestick(fig, filtrado, C)
    _add_smas(fig, filtrado, C)
    _add_bollinger(fig, filtrado, C)
    _add_volume(fig, filtrado, C)
    _add_macd(fig, filtrado, C)
    _add_rsi(fig, filtrado, C)
    _add_willr(fig, filtrado, C)

    fig.update_layout(
        template='plotly_white', paper_bgcolor=C['card_bg'], plot_bgcolor=C['card_bg'],
        font=dict(color=C['text'], family='Inter'),
        title_text=f"Análisis Técnico — {ticker}",
        xaxis_rangeslider_visible=False, height=CHART_HEIGHT,
        margin=dict(t=100, b=50, l=50, r=50)
    )
    fig.update_xaxes(gridcolor=C['grid'], linecolor=C['grid'])
    fig.update_yaxes(gridcolor=C['grid'], linecolor=C['grid'])

    chart_html = fig.to_html(include_plotlyjs='cdn', div_id='grafico')
    tabla_html  = _tabla_html(datos, resultado, ticker, C)
    css         = _css(C)
    fecha       = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Análisis — {ticker}</title>
  {css}
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📊 Análisis Técnico — {ticker}</h1>
      <p>Generado el {fecha} · últimos {MONTHS_DISPLAY} meses en gráficos</p>
    </div>
    <div class="chart-container">{chart_html}</div>
    {tabla_html}
    <div class="footer"><p>Plataforma de Trading · Solo fines informativos</p></div>
  </div>
</body>
</html>"""

    path = os.path.join(out, f"{ticker}_analisis.html")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    logger.info(f"Gráfico guardado: {path}")


# ── Chart helpers ──────────────────────────────────────────────────────────

def _last_n_months(df, n):
    if df.empty: return df
    cutoff = df['fecha'].max() - timedelta(days=n * 30)
    return df[df['fecha'] >= cutoff].copy()

def _add_candlestick(fig, df, C):
    fig.add_trace(go.Candlestick(
        x=df['fecha'], open=df['apertura'], high=df['maximo'],
        low=df['minimo'], close=df['cierre'], name='Precio',
        increasing_line_color=C['buy'], decreasing_line_color=C['sell']
    ), row=1, col=1)

def _add_smas(fig, df, C):
    colors = [C['accent'], '#f59e0b', '#a855f7']
    for i, col in enumerate(['SMA_30', 'SMA_60', 'SMA_90']):
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df['fecha'], y=df[col], name=col,
                line=dict(color=colors[i % 3], width=1.5)), row=1, col=1)

def _add_bollinger(fig, df, C):
    if 'BBU_BB' not in df.columns: return
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['BBU_BB'], showlegend=False,
        line=dict(color='rgba(148,163,184,.3)', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['BBL_BB'], showlegend=False,
        line=dict(color='rgba(148,163,184,.3)', width=1),
        fill='tonexty', fillcolor='rgba(148,163,184,.05)'), row=1, col=1)

def _add_volume(fig, df, C):
    colors = [C['buy'] if c >= o else C['sell'] for c, o in zip(df['cierre'], df['apertura'])]
    fig.add_trace(go.Bar(x=df['fecha'], y=df['volumen'], name='Volumen',
        marker_color=colors, opacity=0.5), row=2, col=1)

def _add_macd(fig, df, C):
    if 'MACD' not in df.columns: return
    bar_colors = [C['buy'] if v >= 0 else C['sell'] for v in df['MACDh']]
    fig.add_trace(go.Bar(x=df['fecha'], y=df['MACDh'], marker_color=bar_colors, showlegend=False), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['MACD'], name='MACD', line=dict(color=C['accent'], width=1.5)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['MACDs'], name='Señal', line=dict(color='#f43f5e', width=1.5)), row=3, col=1)

def _add_rsi(fig, df, C):
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['RSI'], name='RSI',
        line=dict(color='#a855f7', width=2)), row=4, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color=C['sell'], row=4, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=C['buy'],  row=4, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor=C['sell'], opacity=0.05, line_width=0, row=4, col=1)
    fig.add_hrect(y0=0,  y1=30,  fillcolor=C['buy'],  opacity=0.05, line_width=0, row=4, col=1)

def _add_willr(fig, df, C):
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['WILLR'], name='Williams %R',
        line=dict(color='#06b6d4', width=2)), row=5, col=1)
    fig.add_hline(y=-20, line_dash="dash", line_color=C['sell'], row=5, col=1)
    fig.add_hline(y=-80, line_dash="dash", line_color=C['buy'],  row=5, col=1)


def _tabla_html(datos, resultado, ticker, C) -> str:
    senales = resultado.get('señales', {})
    resumen = resultado.get('resumen', 'N/A')
    rc = "signal-buy" if resumen == "COMPRA" else "signal-sell" if resumen == "VENTA" else "signal-hold"

    rows = ""
    for _, row in datos.tail(10).iloc[::-1].iterrows():
        rows += f"""<tr>
          <td>{row['fecha'].strftime('%Y-%m-%d')}</td>
          <td>${row['apertura']:.2f}</td><td>${row['maximo']:.2f}</td>
          <td>${row['minimo']:.2f}</td>
          <td class="precio-cierre">${row['cierre']:.2f}</td>
          <td>{row['volumen']:,.0f}</td>
          <td>{row.get('RSI', 0):.2f}</td><td>{row.get('WILLR', 0):.2f}</td>
          <td>{row.get('MACD', 0):.4f}</td>
        </tr>"""

    sig_rows = ""
    for ind, sig in senales.items():
        sc = "signal-buy" if sig == "COMPRA" else "signal-sell" if sig == "VENTA" else "signal-hold"
        sig_rows += f"<tr><td>{ind.replace('_',' ')}</td><td class='{sc}'>{sig}</td></tr>"

    return f"""
<div class="table-container">
  <div class="recommendation-card">
    <h2>Recomendación</h2>
    <div class="recommendation {rc}">{resumen}</div>
    <p class="recommendation-note">Basado en {len(senales)} indicadores</p>
  </div>
  <div class="data-section">
    <h2>Cotizaciones recientes (10 sesiones)</h2>
    <div class="table-wrapper"><table class="data-table">
      <thead><tr><th>Fecha</th><th>Apertura</th><th>Máximo</th><th>Mínimo</th>
      <th>Cierre</th><th>Volumen</th><th>RSI</th><th>Williams %R</th><th>MACD</th></tr></thead>
      <tbody>{rows}</tbody>
    </table></div>
    <h2 style="margin-top:24px">Señales de indicadores</h2>
    <div class="table-wrapper"><table class="signals-table">
      <thead><tr><th>Indicador</th><th>Señal</th></tr></thead>
      <tbody>{sig_rows}</tbody>
    </table></div>
  </div>
</div>"""


def _css(C) -> str:
    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:{C['background']};color:{C['text']};padding:20px;line-height:1.6}}
.container{{max-width:1400px;margin:0 auto}}
.header{{background:{C['card_bg']};padding:40px;border-radius:24px;margin-bottom:30px;border:1px solid {C['grid']}}}
.header h1{{font-size:2.2em;font-weight:700;color:{C['accent']};margin-bottom:8px}}
.header p{{color:{C['text_muted']}}}
.chart-container{{background:{C['card_bg']};padding:24px;border-radius:24px;margin-bottom:30px;border:1px solid {C['grid']}}}
.table-container{{display:grid;grid-template-columns:320px 1fr;gap:30px;margin-bottom:30px}}
.recommendation-card{{background:{C['card_bg']};padding:32px;border-radius:24px;border:1px solid {C['grid']};text-align:center;height:fit-content}}
.recommendation-card h2{{font-size:1em;text-transform:uppercase;letter-spacing:2px;color:{C['text_muted']};margin-bottom:20px}}
.recommendation{{font-size:3em;font-weight:800;margin:20px 0;padding:10px;border-radius:16px}}
.signal-buy{{color:{C['buy']};background:rgba(16,185,129,.1)}}
.signal-sell{{color:{C['sell']};background:rgba(239,68,68,.1)}}
.signal-hold{{color:{C['hold']};background:rgba(100,116,139,.1)}}
.data-section{{background:{C['card_bg']};padding:32px;border-radius:24px;border:1px solid {C['grid']}}}
.data-section h2{{font-size:1.3em;font-weight:600;margin-bottom:16px}}
.table-wrapper{{overflow-x:auto}}
table{{width:100%;border-collapse:separate;border-spacing:0 6px}}
th{{text-align:left;padding:10px 14px;color:{C['text_muted']};font-weight:600;font-size:.85em;text-transform:uppercase}}
td{{padding:14px;background:rgba(0,0,0,.01)}}
.precio-cierre{{font-weight:700;color:{C['accent']}}}
.footer{{margin-top:50px;padding:30px;text-align:center;color:{C['text_muted']};font-size:.85em;border-top:1px solid {C['grid']}}}
@media(max-width:1100px){{.table-container{{grid-template-columns:1fr}}}}
</style>"""
