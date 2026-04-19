"""Dashboard consolidado HTML para todos los tickers analizados."""

import json
import os
from datetime import datetime
from typing import Dict, List

from trading_platform.core.constants import REPORTS_DIR
from trading_platform.core.logging import get_logger
from trading_platform.visualization.theme import get_theme

logger = get_logger(__name__)


def generar_dashboard_consolidado(ticker_data: List[Dict], output_dir: str = None, theme_name: str = "light") -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = output_dir or str(REPORTS_DIR)
    C = get_theme(theme_name)

    compras, ventas, keeps = [], [], []
    for item in ticker_data:
        res  = item['resultado_analisis']
        datos = item['datos_con_indicadores']
        vol = datos['cierre'].pct_change().std() * 100
        info = {
            'ticker':       res['ticker'],
            'company_name': item['company_name'],
            'precio':       res['precio_cierre'],
            'resumen':      res['resumen'],
            'fecha':        res['fecha'],
            'senales':      res['señales'],
            'rsi':          datos.iloc[-1].get('RSI', 0),
            'willr':        datos.iloc[-1].get('WILLR', 0),
            'macd':         datos.iloc[-1].get('MACD', 0),
            'volatilidad':  vol,
        }
        vals = list(res['señales'].values())
        info['count_compra'] = vals.count('COMPRA')
        info['count_venta']  = vals.count('VENTA')
        info['count_hold']   = vals.count('KEEP/NO SIGNAL')

        if res['resumen'] == 'COMPRA':   compras.append(info)
        elif res['resumen'] == 'VENTA':  ventas.append(info)
        else:                            keeps.append(info)

    compras.sort(key=lambda x: x['count_compra'], reverse=True)
    ventas.sort(key=lambda x: x['count_venta'],   reverse=True)

    html = _html(compras, ventas, keeps, C)
    path = os.path.join(out, "dashboard_consolidado.html")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    logger.info(f"Dashboard guardado: {path}")
    return path


def _row(info: Dict) -> str:
    rc = "row-buy" if info['resumen'] == 'COMPRA' else "row-sell" if info['resumen'] == 'VENTA' else "row-hold"
    badge = "badge-buy" if info['resumen'] == 'COMPRA' else "badge-sell" if info['resumen'] == 'VENTA' else "badge-hold"
    return f"""<tr class="ticker-row {rc}" data-rec="{info['resumen']}"
        onclick="window.open('{info['ticker']}_analisis.html','_blank')">
      <td><strong>{info['ticker']}</strong></td>
      <td>{info['company_name']}</td>
      <td>${info['precio']:.2f}</td>
      <td><span class="badge {badge}">{info['resumen']}</span></td>
      <td>{info['rsi']:.1f}</td>
      <td>{info['willr']:.1f}</td>
      <td>{info['volatilidad']:.2f}%</td>
      <td style="color:#10b981">{info['count_compra']}</td>
      <td style="color:#ef4444">{info['count_venta']}</td>
      <td style="color:#94a3b8">{info['count_hold']}</td>
    </tr>"""


def _html(compras, ventas, keeps, C) -> str:
    todos   = compras + ventas + keeps
    total   = len(todos)
    fecha   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    n_buy   = len(compras)
    n_sell  = len(ventas)
    sentimiento = round(n_buy / max(n_buy + n_sell, 1) * 100, 1)
    scatter  = json.dumps([{'ticker': t['ticker'], 'rsi': t['rsi'], 'willr': t['willr'],
                             'resumen': t['resumen'], 'vol': t['volatilidad']} for t in todos])
    rows_html = "\n".join(_row(t) for t in todos)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Dashboard — Trading Platform</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  {_css_dashboard(C)}
</head>
<body>
<div class="dash">
  <div class="dash-header">
    <h1>📊 Dashboard Consolidado</h1>
    <p class="sub">Actualizado: {fecha}</p>
  </div>
  <div class="kpi-grid">
    <div class="kpi"><div class="kpi-n">{total}</div><div class="kpi-l">Tickers analizados</div></div>
    <div class="kpi buy"><div class="kpi-n">{n_buy}</div><div class="kpi-l">Señales COMPRA</div></div>
    <div class="kpi sell"><div class="kpi-n">{n_sell}</div><div class="kpi-l">Señales VENTA</div></div>
    <div class="kpi"><div class="kpi-n">{sentimiento}%</div><div class="kpi-l">Sentimiento alcista</div></div>
  </div>
  <div class="grid2">
    <div class="card"><h2>🧠 Sentimiento</h2><div id="gauge"></div></div>
    <div class="card"><h2>🔥 Volatilidad</h2><div id="heat"></div></div>
  </div>
  <div class="card full">
    <div class="table-hdr">
      <h2>📋 Activos</h2>
      <div class="controls">
        <input id="search" placeholder="Buscar…" oninput="buscar()">
        <button class="fb active" onclick="filtrar('todos',this)">Todos</button>
        <button class="fb buy" onclick="filtrar('COMPRA',this)">Compra</button>
        <button class="fb sell" onclick="filtrar('VENTA',this)">Venta</button>
      </div>
    </div>
    <div style="overflow-x:auto">
      <table id="tbl">
        <thead><tr>
          <th>Ticker</th><th>Empresa</th><th>Precio</th><th>Rec.</th>
          <th>RSI</th><th>Williams%R</th><th>Volatilidad</th>
          <th>📈</th><th>📉</th><th>━</th>
        </tr></thead>
        <tbody id="tbody">{rows_html}</tbody>
      </table>
    </div>
  </div>
  <div class="card full"><h2>📈 RSI vs Williams %R</h2><div id="scatter"></div></div>
</div>
<script>
const data = {scatter};
const C = {{buy:'#10b981',sell:'#ef4444',acc:'{C["accent"]}',bg:'transparent',grid:'{C["grid"]}',text:'{C["text"]}'}};
Plotly.newPlot('gauge',[{{type:'indicator',mode:'gauge+number',value:{sentimiento},
  title:{{text:'Alcista (%)',font:{{size:16,color:C.text}}}},
  gauge:{{axis:{{range:[0,100]}},bar:{{color:C.acc}},
    steps:[{{range:[0,30],color:'rgba(239,68,68,.15)'}},{{range:[30,70],color:'rgba(100,116,139,.1)'}},{{range:[70,100],color:'rgba(16,185,129,.15)'}}]}}
}}],{{paper_bgcolor:'transparent',margin:{{t:30,b:30,l:30,r:30}},font:{{color:C.text}}}});
Plotly.newPlot('heat',[{{type:'heatmap',x:data.map(d=>d.ticker),y:['Volatilidad'],
  z:[data.map(d=>d.vol)],colorscale:[[0,'rgba(16,185,129,.8)'],[.5,'rgba(245,158,11,.8)'],[1,'rgba(239,68,68,.8)']]
}}],{{paper_bgcolor:'transparent',plot_bgcolor:'transparent',font:{{color:C.text}},margin:{{t:10,b:50,l:80,r:10}},xaxis:{{tickangle:-45}}}});
const traces = ['COMPRA','VENTA','KEEP'].map(r=>{{
  const pts = data.filter(d=>d.resumen===r);
  return {{x:pts.map(d=>d.rsi),y:pts.map(d=>d.willr),text:pts.map(d=>d.ticker),
    mode:'markers+text',textposition:'top center',name:r,
    marker:{{size:12,color:r==='COMPRA'?C.buy:(r==='VENTA'?C.sell:'#64748b'),line:{{width:1,color:'white'}}}}}};
}});
Plotly.newPlot('scatter',traces,{{paper_bgcolor:'transparent',plot_bgcolor:'transparent',
  font:{{color:C.text}},xaxis:{{title:'RSI',gridcolor:C.grid,range:[0,100]}},
  yaxis:{{title:'Williams %R',gridcolor:C.grid,range:[-100,0]}},
  shapes:[
    {{type:'line',x0:30,x1:30,y0:-100,y1:0,line:{{color:C.buy,dash:'dash'}}}},
    {{type:'line',x0:70,x1:70,y0:-100,y1:0,line:{{color:C.sell,dash:'dash'}}}},
    {{type:'line',x0:0,x1:100,y0:-80,y1:-80,line:{{color:C.buy,dash:'dash'}}}},
    {{type:'line',x0:0,x1:100,y0:-20,y1:-20,line:{{color:C.sell,dash:'dash'}}}}
  ]}});
function filtrar(tipo,btn){{
  document.querySelectorAll('.fb').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.ticker-row').forEach(r=>
    r.style.display=(tipo==='todos'||r.dataset.rec===tipo)?'':'none');
}}
function buscar(){{
  const q=document.getElementById('search').value.toUpperCase();
  document.querySelectorAll('.ticker-row').forEach(r=>
    r.style.display=r.innerText.toUpperCase().includes(q)?'':'none');
}}
</script>
</body></html>"""


def _css_dashboard(C) -> str:
    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:{C['background']};color:{C['text']};padding:20px}}
.dash{{max-width:1600px;margin:0 auto;display:flex;flex-direction:column;gap:20px}}
.dash-header{{background:{C['card_bg']};padding:40px;border-radius:24px;border:1px solid {C['grid']}}}
.dash-header h1{{font-size:2.2em;color:{C['accent']};margin-bottom:8px}}
.sub{{color:{C['text_muted']}}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px}}
.kpi{{background:{C['card_bg']};padding:24px;border-radius:20px;border:1px solid {C['grid']};text-align:center}}
.kpi-n{{font-size:2.5em;font-weight:800;color:{C['accent']}}}
.kpi.buy .kpi-n{{color:{C['buy']}}}.kpi.sell .kpi-n{{color:{C['sell']}}}
.kpi-l{{color:{C['text_muted']};text-transform:uppercase;font-size:.8em;margin-top:6px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.card{{background:{C['card_bg']};padding:24px;border-radius:24px;border:1px solid {C['grid']}}}
.card.full{{grid-column:1/-1}}
.card h2{{font-size:1.1em;margin-bottom:16px;color:{C['text_muted']}}}
.table-hdr{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:16px}}
.controls{{display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
#search{{background:{C['background']};border:1px solid {C['grid']};color:{C['text']};padding:8px 16px;border-radius:10px;width:220px}}
.fb{{background:{C['background']};border:1px solid {C['grid']};color:{C['text_muted']};padding:7px 14px;border-radius:10px;cursor:pointer}}
.fb.active{{background:{C['accent']};color:#fff;border-color:{C['accent']}}}
.fb.buy.active{{background:{C['buy']};border-color:{C['buy']}}}
.fb.sell.active{{background:{C['sell']};border-color:{C['sell']}}}
table{{width:100%;border-collapse:separate;border-spacing:0 4px}}
th{{text-align:left;padding:10px 12px;color:{C['text_muted']};font-size:.83em;text-transform:uppercase}}
.ticker-row td{{padding:14px 12px;cursor:pointer}}
.ticker-row:hover td{{background:rgba(0,0,0,.02)}}
.badge{{padding:3px 10px;border-radius:8px;font-size:.78em;font-weight:700}}
.badge-buy{{background:rgba(16,185,129,.12);color:{C['buy']}}}
.badge-sell{{background:rgba(239,68,68,.12);color:{C['sell']}}}
.badge-hold{{background:rgba(100,116,139,.12);color:{C['hold']}}}
@media(max-width:900px){{.grid2{{grid-template-columns:1fr}}}}
</style>"""
