"""Generador de Dashboard Consolidado Multi-Panel para Análisis de Trading."""

import os
from datetime import datetime
from typing import List, Dict
import json
from logger_config import get_logger

logger = get_logger(__name__)


def generar_dashboard_consolidado(ticker_data_collection: List[Dict], output_dir: str = "salidas"):
    """
    Genera un dashboard HTML consolidado con todos los análisis.

    Args:
        ticker_data_collection: Lista de diccionarios con datos de análisis de cada ticker
        output_dir: Directorio de salida
    """
    logger.info("Generando dashboard consolidado...")

    # Preparar datos
    compras = []
    ventas = []
    keeps = []

    for data in ticker_data_collection:
        resultado = data['resultado_analisis']
        company_name = data['company_name']
        datos = data['datos_con_indicadores']

        # Calcular volatilidad (desviación estándar del cierre)
        volatilidad = datos['cierre'].pct_change().std() * 100
        
        ticker_info = {
            'ticker': resultado['ticker'],
            'company_name': company_name,
            'precio': resultado['precio_cierre'],
            'resumen': resultado['resumen'],
            'fecha': resultado['fecha'],
            'senales': resultado['señales'],
            'rsi': datos.iloc[-1]['RSI'],
            'willr': datos.iloc[-1]['WILLR'],
            'macd': datos.iloc[-1]['MACD_12_26_9'],
            'volumen': datos.iloc[-1]['volumen'],
            'volatilidad': volatilidad
        }

        # Contar señales
        senales_vals = list(resultado['señales'].values())
        ticker_info['count_compra'] = senales_vals.count('COMPRA')
        ticker_info['count_venta'] = senales_vals.count('VENTA')
        ticker_info['count_hold'] = senales_vals.count('KEEP/NO SIGNAL')

        if resultado['resumen'] == 'COMPRA':
            compras.append(ticker_info)
        elif resultado['resumen'] == 'VENTA':
            ventas.append(ticker_info)
        else:
            keeps.append(ticker_info)

    # Ordenar por número de señales
    compras.sort(key=lambda x: x['count_compra'], reverse=True)
    ventas.sort(key=lambda x: x['count_venta'], reverse=True)

    # Generar HTML
    html_content = _generar_html_dashboard(compras, ventas, keeps, ticker_data_collection)

    # Guardar
    output_path = os.path.join(output_dir, "dashboard_consolidado.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"Dashboard consolidado generado: {output_path}")
    return output_path


def _generar_fila_tabla(ticker_info: Dict) -> str:
    """Genera HTML para una fila de la tabla de tickers."""
    resumen_class = "row-buy" if ticker_info['resumen'] == 'COMPRA' else \
                   "row-sell" if ticker_info['resumen'] == 'VENTA' else "row-hold"

    # Iconos para indicadores
    rsi_status = "🟢" if ticker_info['rsi'] < 30 else "🔴" if ticker_info['rsi'] > 70 else "🟡"
    willr_status = "🟢" if ticker_info['willr'] < -80 else "🔴" if ticker_info['willr'] > -20 else "🟡"
    macd_status = "🟢" if ticker_info['macd'] > 0 else "🔴"

    return f"""
    <tr class="ticker-row {resumen_class}" data-recommendation="{ticker_info['resumen']}"
        onclick="window.open('{ticker_info['ticker']}_analisis.html', '_blank')">
        <td class="ticker-col"><strong>{ticker_info['ticker']}</strong></td>
        <td class="company-col">{ticker_info['company_name']}</td>
        <td class="price-col">${ticker_info['precio']:.2f}</td>
        <td class="recommendation-col">
            <span class="badge badge-{resumen_class}">{ticker_info['resumen']}</span>
        </td>
        <td class="indicator-col">{ticker_info['rsi']:.1f}</td>
        <td class="indicator-col">{ticker_info['willr']:.1f}</td>
        <td class="indicator-col">{ticker_info['volatilidad']:.2f}%</td>
        <td class="signal-col"><span class="signal-buy">{ticker_info['count_compra']}</span></td>
        <td class="signal-col"><span class="signal-sell">{ticker_info['count_venta']}</span></td>
        <td class="signal-col"><span class="signal-hold">{ticker_info['count_hold']}</span></td>
    </tr>
    """


def _generar_html_dashboard(compras: List[Dict], ventas: List[Dict],
                            keeps: List[Dict], all_data: List[Dict]) -> str:
    """Genera el HTML completo del dashboard."""

    total_tickers = len(compras) + len(ventas) + len(keeps)
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Generar todas las filas de la tabla
    todos_tickers = compras + ventas + keeps
    filas_tabla_html = "\n".join([_generar_fila_tabla(t) for t in todos_tickers])

    # Top 5 compras y ventas
    top_compras_html = ""
    for i, ticker in enumerate(compras[:5], 1):
        top_compras_html += f"""
        <div class="top-item" onclick="window.open('{ticker['ticker']}_analisis.html', '_blank')">
            <span class="top-number">{i}</span>
            <span class="top-ticker">{ticker['ticker']}</span>
            <span class="top-signals">{ticker['count_compra']} señales</span>
        </div>
        """

    top_ventas_html = ""
    for i, ticker in enumerate(ventas[:5], 1):
        top_ventas_html += f"""
        <div class="top-item" onclick="window.open('{ticker['ticker']}_analisis.html', '_blank')">
            <span class="top-number">{i}</span>
            <span class="top-ticker">{ticker['ticker']}</span>
            <span class="top-signals">{ticker['count_venta']} señales</span>
        </div>
        """

    # Preparar datos para el scatter plot y heatmap
    scatter_data = []
    for ticker in todos_tickers:
        scatter_data.append({
            'ticker': ticker['ticker'],
            'rsi': ticker['rsi'],
            'willr': ticker['willr'],
            'resumen': ticker['resumen'],
            'volatilidad': ticker['volatilidad']
        })

    scatter_json = json.dumps(scatter_data)
    
    # Calcular sentimiento
    total_signals = len(compras) + len(ventas)
    sentiment_value = (len(compras) / total_signals * 100) if total_signals > 0 else 50

    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Consolidado - Trading Platform</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    {_generar_css_dashboard()}
</head>
<body>
    <div class="dashboard-container">
        <!-- Header -->
        <div class="dashboard-header">
            <h1>📊 Dashboard Consolidado de Trading</h1>
            <p class="header-date">Actualizado: {fecha_actual}</p>
        </div>

        <!-- Summary Panel -->
        <div class="summary-panel">
            <div class="summary-item">
                <div class="summary-label">Tickers Analizados</div>
                <div class="summary-number">{total_tickers}</div>
            </div>
            <div class="summary-item buy-summary">
                <div class="summary-label">Señales COMPRA</div>
                <div class="summary-number">{len(compras)}</div>
            </div>
            <div class="summary-item sell-summary">
                <div class="summary-label">Señales VENTA</div>
                <div class="summary-number">{len(ventas)}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Sentimiento Alcista</div>
                <div class="summary-number">{sentiment_value:.1f}%</div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="dashboard-grid">
            <!-- Sentiment Gauge -->
            <div class="card">
                <h2>🧠 Sentimiento del Mercado</h2>
                <div id="sentimentGauge"></div>
            </div>

            <!-- Volatility Heatmap -->
            <div class="card">
                <h2>🔥 Mapa de Volatilidad</h2>
                <div id="volatilityHeatmap"></div>
            </div>

            <!-- Ticker Table -->
            <div class="card full-width">
                <div class="table-header">
                    <h2>📋 Listado de Activos</h2>
                    <div class="table-controls">
                        <input type="text" id="searchInput" placeholder="Buscar ticker o empresa..." onkeyup="buscarTicker()">
                        <div class="filter-group">
                            <button class="filter-btn active" onclick="filtrarPor('todos')">Todos</button>
                            <button class="filter-btn filter-buy" onclick="filtrarPor('COMPRA')">Compra</button>
                            <button class="filter-btn filter-sell" onclick="filtrarPor('VENTA')">Venta</button>
                        </div>
                    </div>
                </div>
                <div class="table-container">
                    <table id="tickerTable" class="ticker-table">
                        <thead>
                            <tr>
                                <th onclick="sortTable(0)">Ticker ↕</th>
                                <th onclick="sortTable(1)">Empresa ↕</th>
                                <th onclick="sortTable(2)">Precio ↕</th>
                                <th onclick="sortTable(3)">Recomendación ↕</th>
                                <th onclick="sortTable(4)">RSI ↕</th>
                                <th onclick="sortTable(5)">Williams %R ↕</th>
                                <th onclick="sortTable(6)">Volatilidad ↕</th>
                                <th onclick="sortTable(7)">📈 ↕</th>
                                <th onclick="sortTable(8)">📉 ↕</th>
                                <th onclick="sortTable(9)">━ ↕</th>
                            </tr>
                        </thead>
                        <tbody id="tickerTableBody">
                            {filas_tabla_html}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Scatter Plot -->
            <div class="card full-width">
                <h2>📈 RSI vs Williams %R (Zonas de Extremo)</h2>
                <div id="scatterPlot"></div>
            </div>
        </div>
    </div>
    </div>

    <script>
        const scatterData = {scatter_json};
        const theme = {{
            bg: '#ffffff',
            text: '#1e293b',
            grid: '#e2e8f0',
            buy: '#10b981',
            sell: '#ef4444',
            accent: '#0284c7'
        }};

        // Sentiment Gauge
        const gaugeData = [{{
            domain: {{ x: [0, 1], y: [0, 1] }},
            value: {sentiment_value},
            title: {{ text: "Sentimiento Alcista (%)", font: {{ size: 18, color: theme.text }} }},
            type: "indicator",
            mode: "gauge+number",
            gauge: {{
                axis: {{ range: [0, 100], tickwidth: 1, tickcolor: theme.text }},
                bar: {{ color: theme.accent }},
                bgcolor: theme.bg,
                borderwidth: 2,
                bordercolor: theme.grid,
                steps: [
                    {{ range: [0, 30], color: "rgba(239, 68, 68, 0.2)" }},
                    {{ range: [30, 70], color: "rgba(100, 116, 139, 0.2)" }},
                    {{ range: [70, 100], color: "rgba(16, 185, 129, 0.2)" }}
                ],
                threshold: {{
                    line: {{ color: "white", width: 4 }},
                    thickness: 0.75,
                    value: {sentiment_value}
                }}
            }}
        }}];

        Plotly.newPlot('sentimentGauge', gaugeData, {{ 
            paper_bgcolor: 'transparent', 
            font: {{ color: theme.text }},
            margin: {{ t: 30, b: 30, l: 30, r: 30 }}
        }});

        // Volatility Heatmap
        const heatmapData = [{{
            x: scatterData.map(d => d.ticker),
            y: ['Volatilidad'],
            z: [scatterData.map(d => d.volatilidad)],
            type: 'heatmap',
            colorscale: [
                [0, 'rgba(16, 185, 129, 0.8)'],
                [0.5, 'rgba(245, 158, 11, 0.8)'],
                [1, 'rgba(239, 68, 68, 0.8)']
            ],
            showscale: true
        }}];

        Plotly.newPlot('volatilityHeatmap', heatmapData, {{
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: {{ color: theme.text }},
            margin: {{ t: 10, b: 50, l: 80, r: 10 }},
            xaxis: {{ tickangle: -45 }}
        }});

        // Scatter Plot
        const traces = ['COMPRA', 'VENTA', 'KEEP'].map(res => ({{
            x: scatterData.filter(d => d.resumen === res).map(d => d.rsi),
            y: scatterData.filter(d => d.resumen === res).map(d => d.willr),
            text: scatterData.filter(d => d.resumen === res).map(d => d.ticker),
            mode: 'markers+text',
            textposition: 'top center',
            name: res,
            marker: {{ 
                size: 12, 
                color: res === 'COMPRA' ? theme.buy : (res === 'VENTA' ? theme.sell : '#64748b'),
                line: {{ width: 1, color: 'white' }}
            }}
        }}));

        Plotly.newPlot('scatterPlot', traces, {{
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: {{ color: theme.text }},
            xaxis: {{ title: 'RSI', gridcolor: theme.grid, range: [0, 100] }},
            yaxis: {{ title: 'Williams %R', gridcolor: theme.grid, range: [-100, 0] }},
            shapes: [
                {{ type: 'line', x0: 30, x1: 30, y0: -100, y1: 0, line: {{ color: theme.buy, dash: 'dash' }} }},
                {{ type: 'line', x0: 70, x1: 70, y0: -100, y1: 0, line: {{ color: theme.sell, dash: 'dash' }} }},
                {{ type: 'line', x0: 0, x1: 100, y0: -80, y1: -80, line: {{ color: theme.buy, dash: 'dash' }} }},
                {{ type: 'line', x0: 0, x1: 100, y0: -20, y1: -20, line: {{ color: theme.sell, dash: 'dash' }} }}
            ]
        }});

        // Interactivity Functions
        function filtrarPor(tipo) {{
            const rows = document.querySelectorAll('.ticker-row');
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            rows.forEach(row => row.style.display = (tipo === 'todos' || row.dataset.recommendation === tipo) ? '' : 'none');
        }}

        function buscarTicker() {{
            const filter = document.getElementById('searchInput').value.toUpperCase();
            document.querySelectorAll('.ticker-row').forEach(row => {{
                const text = row.innerText.toUpperCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            }});
        }}

        function sortTable(n) {{
            const table = document.getElementById("tickerTable");
            let rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            switching = true;
            dir = "asc";
            while (switching) {{
                switching = false;
                rows = table.rows;
                for (i = 1; i < (rows.length - 1); i++) {{
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName("TD")[n];
                    y = rows[i + 1].getElementsByTagName("TD")[n];
                    let xVal = x.innerText.replace('$', '').replace('%', '');
                    let yVal = y.innerText.replace('$', '').replace('%', '');
                    if (!isNaN(parseFloat(xVal))) {{
                        xVal = parseFloat(xVal);
                        yVal = parseFloat(yVal);
                    }}
                    if (dir == "asc") {{
                        if (xVal > yVal) {{ shouldSwitch = true; break; }}
                    }} else if (dir == "desc") {{
                        if (xVal < yVal) {{ shouldSwitch = true; break; }}
                    }}
                }}
                if (shouldSwitch) {{
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount++;
                }} else {{
                    if (switchcount == 0 && dir == "asc") {{ dir = "desc"; switching = true; }}
                }}
            }}
        }}
    </script>
</body>
</html>
    """


def _generar_css_dashboard() -> str:
    """Genera el CSS para el dashboard."""
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            padding: 20px;
            line-height: 1.6;
        }

        .dashboard-container {
            max-width: 1600px;
            margin: 0 auto;
        }

        .dashboard-header {
            background: #ffffff;
            padding: 40px;
            border-radius: 24px;
            margin-bottom: 20px;
            border: 1px solid #e2e8f0;
            text-align: left;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }

        .dashboard-header h1 {
            font-size: 2.5em;
            color: #0284c7;
            margin-bottom: 8px;
        }

        .header-date {
            color: #64748b;
        }

        .summary-panel {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .summary-item {
            background: #ffffff;
            padding: 24px;
            border-radius: 20px;
            border: 1px solid #e2e8f0;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }

        .summary-number {
            font-size: 2.5em;
            font-weight: 800;
            color: #0284c7;
        }

        .buy-summary .summary-number { color: #10b981; }
        .sell-summary .summary-number { color: #ef4444; }

        .summary-label {
            color: #64748b;
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 1px;
            margin-top: 8px;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }

        .card {
            background: #ffffff;
            padding: 24px;
            border-radius: 24px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }

        .full-width {
            grid-column: 1 / -1;
        }

        .card h2 {
            font-size: 1.2em;
            margin-bottom: 20px;
            color: #64748b;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }

        .table-controls {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        #searchInput {
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            color: #1e293b;
            padding: 10px 20px;
            border-radius: 12px;
            width: 300px;
        }

        .filter-group {
            display: flex;
            gap: 8px;
        }

        .filter-btn {
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            color: #64748b;
            padding: 8px 16px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .filter-btn.active {
            background: #0284c7;
            color: #ffffff;
            border-color: #0284c7;
            font-weight: 600;
        }

        .ticker-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 4px;
        }

        .ticker-table th {
            text-align: left;
            padding: 12px;
            color: #64748b;
            font-size: 0.85em;
            text-transform: uppercase;
            cursor: pointer;
        }

        .ticker-table th:hover { color: #0284c7; }

        .ticker-row {
            cursor: pointer;
            transition: transform 0.2s;
        }

        .ticker-row:hover {
            transform: scale(1.005);
            background: rgba(0,0,0,0.01);
        }

        .ticker-row td {
            padding: 16px 12px;
            background: rgba(0,0,0,0.005);
        }

        .ticker-col { color: #0284c7; font-weight: 700; }
        
        .badge {
            padding: 4px 12px;
            border-radius: 8px;
            font-size: 0.8em;
            font-weight: 700;
        }

        .badge-row-buy { background: rgba(16, 185, 129, 0.1); color: #10b981; }
        .badge-row-sell { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
        .badge-row-hold { background: rgba(100, 116, 139, 0.1); color: #64748b; }

        .signal-buy { color: #10b981; }
        .signal-sell { color: #ef4444; }

        @media (max-width: 1000px) {
            .dashboard-grid { grid-template-columns: 1fr; }
            #searchInput { width: 100%; }
        }
    </style>
    """
