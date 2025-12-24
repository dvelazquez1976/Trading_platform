"""Módulo para generación de gráficos interactivos de análisis técnico."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict
import os
from datetime import datetime, timedelta
from logger_config import get_logger

logger = get_logger(__name__)

# Constantes de configuración de gráficos
CHART_HEIGHT = 1000
MONTHS_TO_DISPLAY = 24
CHART_CONFIG = {
    'price_row': 1,
    'volume_row': 2,
    'macd_row': 3,
    'rsi_row': 4,
    'willr_row': 5,
    'row_heights': [0.45, 0.1, 0.15, 0.15, 0.15],
    'vertical_spacing': 0.03
}

# Colores del tema Soft Fintech (Claro)
COLORS = {
    'background': '#f8fafc',  # Slate 50
    'card_bg': '#ffffff',     # White
    'text': '#1e293b',        # Slate 800
    'text_muted': '#64748b',  # Slate 500
    'buy': '#10b981',         # Emerald 500
    'sell': '#ef4444',        # Red 500
    'hold': '#94a3b8',        # Slate 400
    'accent': '#0284c7',      # Sky 700
    'grid': '#e2e8f0'         # Slate 200
}


def _crear_estructura_grafico(ticker: str) -> go.Figure:
    """
    Crea la estructura base del gráfico con subplots.

    Args:
        ticker: Ticker de la acción

    Returns:
        Figura de Plotly configurada
    """
    return make_subplots(
        rows=5,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=CHART_CONFIG['vertical_spacing'],
        subplot_titles=(
            f'📈 {ticker} - Velas y Bandas de Bollinger', 
            '📊 Volumen', 
            '📉 MACD', 
            '🟣 RSI', 
            '🌊 Williams %R'
        ),
        row_heights=CHART_CONFIG['row_heights']
    )

def _agregar_candlestick(fig: go.Figure, datos: pd.DataFrame):
    """Agrega gráfico de velas japonesas."""
    fig.add_trace(
        go.Candlestick(
            x=datos['fecha'],
            open=datos['apertura'],
            high=datos['maximo'],
            low=datos['minimo'],
            close=datos['cierre'],
            name='Precio',
            increasing_line_color=COLORS['buy'],
            decreasing_line_color=COLORS['sell']
        ),
        row=CHART_CONFIG['price_row'], col=1
    )

def _agregar_medias_moviles(fig: go.Figure, datos: pd.DataFrame):
    """Agrega líneas de medias móviles y bandas de Bollinger al gráfico."""
    # SMA 30
    fig.add_trace(
        go.Scatter(
            x=datos['fecha'],
            y=datos['SMA_30'],
            name='SMA 30',
            line=dict(color=COLORS['accent'], width=1.5)
        ),
        row=CHART_CONFIG['price_row'], col=1
    )

    # SMA 60
    fig.add_trace(
        go.Scatter(
            x=datos['fecha'],
            y=datos['SMA_60'],
            name='SMA 60',
            line=dict(color='#f59e0b', width=1.5)  # Amber 500
        ),
        row=CHART_CONFIG['price_row'], col=1
    )

    # Bollinger Bands
    if 'BBU_BB' in datos.columns:
        fig.add_trace(
            go.Scatter(
                x=datos['fecha'], y=datos['BBU_BB'],
                name='Banda Superior',
                line=dict(color='rgba(148, 163, 184, 0.3)', width=1),
                showlegend=False
            ),
            row=CHART_CONFIG['price_row'], col=1
        )
        fig.add_trace(
            go.Scatter(
                x=datos['fecha'], y=datos['BBL_BB'],
                name='Banda Inferior',
                line=dict(color='rgba(148, 163, 184, 0.3)', width=1),
                fill='tonexty',
                fillcolor='rgba(148, 163, 184, 0.05)',
                showlegend=False
            ),
            row=CHART_CONFIG['price_row'], col=1
        )


def _agregar_volumen(fig: go.Figure, datos: pd.DataFrame):
    """Agrega gráfico de barras de volumen."""
    colors = [COLORS['buy'] if c >= o else COLORS['sell'] 
              for c, o in zip(datos['cierre'], datos['apertura'])]
    
    fig.add_trace(
        go.Bar(
            x=datos['fecha'],
            y=datos['volumen'],
            name='Volumen',
            marker_color=colors,
            opacity=0.5
        ),
        row=CHART_CONFIG['volume_row'], col=1
    )

def _agregar_macd(fig: go.Figure, datos: pd.DataFrame):
    """Agrega indicador MACD."""
    if 'MACD' in datos.columns:
        # Histograma
        colors = [COLORS['buy'] if val >= 0 else COLORS['sell'] 
                  for val in datos['MACDh']]
        
        fig.add_trace(
            go.Bar(
                x=datos['fecha'], y=datos['MACDh'],
                name='Histograma',
                marker_color=colors,
                showlegend=False
            ),
            row=CHART_CONFIG['macd_row'], col=1
        )
        
        # Línea MACD
        fig.add_trace(
            go.Scatter(
                x=datos['fecha'], y=datos['MACD'],
                name='MACD',
                line=dict(color=COLORS['accent'], width=1.5)
            ),
            row=CHART_CONFIG['macd_row'], col=1
        )
        
        # Línea de Señal
        fig.add_trace(
            go.Scatter(
                x=datos['fecha'], y=datos['MACDs'],
                name='Señal',
                line=dict(color='#f43f5e', width=1.5) # Rose 500
            ),
            row=CHART_CONFIG['macd_row'], col=1
        )


def _agregar_rsi(fig: go.Figure, datos: pd.DataFrame):
    """Agrega indicador RSI con líneas de referencia."""
    fig.add_trace(
        go.Scatter(
            x=datos['fecha'],
            y=datos['RSI'],
            name='RSI',
            line=dict(color='#a855f7', width=2) # Purple 500
        ),
        row=CHART_CONFIG['rsi_row'], col=1
    )

    # Líneas de referencia
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS['sell'], row=CHART_CONFIG['rsi_row'], col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS['buy'], row=CHART_CONFIG['rsi_row'], col=1)
    
    # Relleno de zonas extremas
    fig.add_hrect(y0=70, y1=100, fillcolor=COLORS['sell'], opacity=0.05, line_width=0, row=CHART_CONFIG['rsi_row'], col=1)
    fig.add_hrect(y0=0, y1=30, fillcolor=COLORS['buy'], opacity=0.05, line_width=0, row=CHART_CONFIG['rsi_row'], col=1)

def _agregar_williams_r(fig: go.Figure, datos: pd.DataFrame):
    """Agrega indicador Williams %R con líneas de referencia."""
    fig.add_trace(
        go.Scatter(
            x=datos['fecha'],
            y=datos['WILLR'],
            name='Williams %R',
            line=dict(color='#06b6d4', width=2) # Cyan 500
        ),
        row=CHART_CONFIG['willr_row'], col=1
    )

    # Líneas de referencia
    fig.add_hline(y=-20, line_dash="dash", line_color=COLORS['sell'], row=CHART_CONFIG['willr_row'], col=1)
    fig.add_hline(y=-80, line_dash="dash", line_color=COLORS['buy'], row=CHART_CONFIG['willr_row'], col=1)


def _filtrar_ultimos_meses(datos: pd.DataFrame, meses: int = MONTHS_TO_DISPLAY) -> pd.DataFrame:
    """
    Filtra el DataFrame para mostrar solo los últimos N meses.

    Args:
        datos: DataFrame con columna 'fecha'
        meses: Número de meses a mostrar

    Returns:
        DataFrame filtrado
    """
    if len(datos) == 0:
        return datos

    fecha_fin = datos['fecha'].max()
    fecha_inicio = fecha_fin - timedelta(days=meses * 30)  # Aproximadamente meses * 30 días

    datos_filtrados = datos[datos['fecha'] >= fecha_inicio].copy()
    logger.debug(f"Datos filtrados: {len(datos_filtrados)} registros de los últimos {meses} meses")

    return datos_filtrados


def _generar_html_tabla(datos: pd.DataFrame, resultado_analisis: Dict, ticker: str) -> str:
    """
    Genera una tabla HTML con cotizaciones, osciladores y recomendaciones.

    Args:
        datos: DataFrame con datos históricos e indicadores
        resultado_analisis: Diccionario con resultados del análisis
        ticker: Ticker de la acción

    Returns:
        String con HTML de la tabla
    """
    # Obtener últimos 10 registros para la tabla
    ultimos_datos = datos.tail(10).copy()
    ultimos_datos = ultimos_datos.iloc[::-1]  # Invertir para mostrar más recientes primero

    # Señales del análisis
    senales = resultado_analisis.get('señales', {})
    resumen = resultado_analisis.get('resumen', 'N/A')

    # Crear tabla de datos recientes
    filas_datos = ""
    for idx, row in ultimos_datos.iterrows():
        fecha_str = row['fecha'].strftime('%Y-%m-%d')
        filas_datos += f"""
        <tr>
            <td>{fecha_str}</td>
            <td>${row['apertura']:.2f}</td>
            <td>${row['maximo']:.2f}</td>
            <td>${row['minimo']:.2f}</td>
            <td class="precio-cierre">${row['cierre']:.2f}</td>
            <td>{row['volumen']:,.0f}</td>
            <td>{row['RSI']:.2f}</td>
            <td>{row['WILLR']:.2f}</td>
            <td>{row['MACD']:.4f}</td>
        </tr>
        """

    # Determinar color del resumen
    resumen_class = ""
    if resumen == "COMPRA":
        resumen_class = "signal-buy"
    elif resumen == "VENTA":
        resumen_class = "signal-sell"
    else:
        resumen_class = "signal-hold"

    # Crear tabla de señales
    filas_senales = ""
    for indicador, senal in senales.items():
        senal_class = ""
        if senal == "COMPRA":
            senal_class = "signal-buy"
        elif senal == "VENTA":
            senal_class = "signal-sell"
        else:
            senal_class = "signal-hold"

        indicador_legible = indicador.replace("_", " ")
        filas_senales += f"""
        <tr>
            <td>{indicador_legible}</td>
            <td class="{senal_class}">{senal}</td>
        </tr>
        """

    html_tabla = f"""
    <div class="table-container">
        <div class="recommendation-card">
            <h2>Recomendación General</h2>
            <div class="recommendation {resumen_class}">
                {resumen}
            </div>
            <p class="recommendation-note">
                Basado en {len(senales)} indicadores técnicos
            </p>
        </div>

        <div class="data-section">
            <h2>Cotizaciones Recientes (Últimos 10 días)</h2>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>Apertura</th>
                            <th>Máximo</th>
                            <th>Mínimo</th>
                            <th>Cierre</th>
                            <th>Volumen</th>
                            <th>RSI</th>
                            <th>Williams %R</th>
                            <th>MACD</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_datos}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="signals-section">
            <h2>Señales de Indicadores</h2>
            <div class="table-wrapper">
                <table class="signals-table">
                    <thead>
                        <tr>
                            <th>Indicador</th>
                            <th>Señal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_senales}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """

    return html_tabla


def _generar_css_moderno() -> str:
    """
    Genera CSS moderno para el HTML.

    Returns:
        String con estilos CSS
    """
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: {COLORS['background']};
            color: {COLORS['text']};
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: {COLORS['card_bg']};
            padding: 40px;
            border-radius: 24px;
            margin-bottom: 30px;
            border: 1px solid {COLORS['grid']};
            text-align: left;
            position: relative;
            overflow: hidden;
        }}

        .header::after {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 300px;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(2, 132, 199, 0.05));
        }}

        .header h1 {{
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 8px;
            color: {COLORS['accent']};
        }}

        .header p {{
            color: {COLORS['text_muted']};
            font-size: 1.1em;
        }}

        .chart-container {{
            background: {COLORS['card_bg']};
            padding: 24px;
            border-radius: 24px;
            margin-bottom: 30px;
            border: 1px solid {COLORS['grid']};
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        }}

        .table-container {{
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 30px;
        }}

        .recommendation-card {{
            background: {COLORS['card_bg']};
            padding: 32px;
            border-radius: 24px;
            border: 1px solid {COLORS['grid']};
            text-align: center;
            height: fit-content;
        }}

        .recommendation-card h2 {{
            font-size: 1.2em;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: {COLORS['text_muted']};
            margin-bottom: 24px;
        }}

        .recommendation {{
            font-size: 3.5em;
            font-weight: 800;
            margin: 20px 0;
            padding: 10px;
            border-radius: 16px;
        }}

        .signal-buy {{ color: {COLORS['buy']}; background: rgba(16, 185, 129, 0.1); }}
        .signal-sell {{ color: {COLORS['sell']}; background: rgba(239, 68, 68, 0.1); }}
        .signal-hold {{ color: {COLORS['hold']}; background: rgba(100, 116, 139, 0.1); }}

        .data-section, .signals-section {{
            background: {COLORS['card_bg']};
            padding: 32px;
            border-radius: 24px;
            border: 1px solid {COLORS['grid']};
        }}

        h2 {{
            font-size: 1.5em;
            font-weight: 600;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .table-wrapper {{
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 8px;
        }}

        th {{
            text-align: left;
            padding: 12px 16px;
            color: {COLORS['text_muted']};
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
        }}

        td {{
            padding: 16px;
            background: rgba(0,0,0,0.01);
        }}

        tr td:first-child {{ border-radius: 12px 0 0 12px; }}
        tr td:last-child {{ border-radius: 0 12px 12px 0; }}

        .precio-cierre {{
            font-weight: 700;
            color: {COLORS['accent']};
        }}

        .footer {{
            margin-top: 50px;
            padding: 40px;
            text-align: center;
            color: {COLORS['text_muted']};
            font-size: 0.9em;
            border-top: 1px solid {COLORS['grid']};
        }}

        @media (max-width: 1100px) {{
            .table-container {{ grid-template-columns: 1fr; }}
        }}
    </style>
    """


def generar_grafico(datos_historicos: pd.DataFrame, resultado_analisis: Dict,
                   ticker: str, output_dir: str = "salidas"):
    """
    Genera un gráfico interactivo con los datos históricos y los resultados del análisis.

    Args:
        datos_historicos: DataFrame con los datos de precios e indicadores
        resultado_analisis: Diccionario con los resultados del análisis
        ticker: Ticker de la acción
        output_dir: Directorio de salida para el archivo HTML (por defecto carpeta "salidas")
    """
    logger.info(f"Generando gráfico interactivo para {ticker}")
    logger.debug(f"Directorio de salida: {output_dir}")
    logger.debug(f"Datos históricos: {len(datos_historicos)} registros")

    try:
        # Crear el directorio de salida si no existe
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Directorio de salida verificado/creado: {output_dir}")

        # Filtrar datos a los últimos 24 meses para el gráfico
        datos_filtrados = _filtrar_ultimos_meses(datos_historicos, MONTHS_TO_DISPLAY)
        logger.info(f"Mostrando datos de los últimos {MONTHS_TO_DISPLAY} meses ({len(datos_filtrados)} registros)")

        # Crear estructura base
        fig = _crear_estructura_grafico(ticker)
        logger.debug("Estructura base del gráfico creada")

        # Agregar componentes del gráfico con datos filtrados
        _agregar_candlestick(fig, datos_filtrados)
        logger.debug("Candlestick agregado")

        _agregar_medias_moviles(fig, datos_filtrados)
        logger.debug("Medias móviles agregadas")

        _agregar_volumen(fig, datos_filtrados)
        logger.debug("Volumen agregado")

        _agregar_macd(fig, datos_filtrados)
        logger.debug("MACD agregado")

        _agregar_rsi(fig, datos_filtrados)
        logger.debug("RSI agregado")

        _agregar_williams_r(fig, datos_filtrados)
        logger.debug("Williams %R agregado")

        # Configurar layout final con tema claro
        fig.update_layout(
            template='plotly_white',
            paper_bgcolor=COLORS['card_bg'],
            plot_bgcolor=COLORS['card_bg'],
            font=dict(color=COLORS['text'], family='Inter'),
            title_text=f"Análisis Técnico - {ticker}",
            xaxis_rangeslider_visible=False,
            height=CHART_HEIGHT,
            margin=dict(t=100, b=50, l=50, r=50)
        )
        
        # Actualizar ejes
        fig.update_xaxes(gridcolor=COLORS['grid'], linecolor=COLORS['grid'])
        fig.update_yaxes(gridcolor=COLORS['grid'], linecolor=COLORS['grid'])
        logger.debug("Layout del gráfico configurado")

        # Generar HTML del gráfico
        grafico_html = fig.to_html(include_plotlyjs='cdn', div_id='grafico')
        logger.debug("HTML del gráfico generado")

        # Generar tabla HTML con datos
        tabla_html = _generar_html_tabla(datos_historicos, resultado_analisis, ticker)
        logger.debug("Tabla HTML generada")

        # Obtener CSS moderno
        css_html = _generar_css_moderno()

        # Combinar todo en un HTML completo
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html_completo = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis Técnico - {ticker}</title>
    {css_html}
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Análisis Técnico - {ticker}</h1>
            <p>Análisis generado el {fecha_actual}</p>
        </div>

        <div class="content">
            <div class="chart-container">
                {grafico_html}
            </div>

            {tabla_html}
        </div>

        <div class="footer">
            <p>Plataforma de Trading Profesional | Los datos son solo para fines informativos</p>
            <p>Mostrando datos de los últimos {MONTHS_TO_DISPLAY} meses en gráficos</p>
        </div>
    </div>
</body>
</html>
        """

        # Guardar archivo HTML completo
        output_path = os.path.join(output_dir, f"{ticker}_analisis.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_completo)

        logger.info(f"Gráfico y análisis generados exitosamente: {output_path}")

    except Exception as e:
        logger.error(f"Error generando gráfico para {ticker}: {e}", exc_info=True)
        raise
