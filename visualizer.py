"""Módulo para generación de gráficos interactivos de análisis técnico."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict
import os
from logger_config import get_logger

logger = get_logger(__name__)

# Constantes de configuración de gráficos
CHART_HEIGHT = 800
CHART_CONFIG = {
    'price_row': 1,
    'volume_row': 2,
    'rsi_row': 3,
    'willr_row': 4,
    'row_heights': [0.6, 0.1, 0.15, 0.15],
    'vertical_spacing': 0.02
}

# Umbrales de indicadores para líneas de referencia
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
WILLR_OVERBOUGHT = -20
WILLR_OVERSOLD = -80


def _crear_estructura_grafico(ticker: str) -> go.Figure:
    """
    Crea la estructura base del gráfico con subplots.

    Args:
        ticker: Ticker de la acción

    Returns:
        Figura de Plotly configurada
    """
    return make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=CHART_CONFIG['vertical_spacing'],
        subplot_titles=(f'{ticker} Candlestick', 'Volumen', 'RSI', 'Williams %R'),
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
            name='Precio'
        ),
        row=CHART_CONFIG['price_row'], col=1
    )


def _agregar_medias_moviles(fig: go.Figure, datos: pd.DataFrame):
    """Agrega líneas de medias móviles al gráfico."""
    fig.add_trace(
        go.Scatter(
            x=datos['fecha'],
            y=datos['SMA_30'],
            name='SMA 30',
            line=dict(color='blue', width=1)
        ),
        row=CHART_CONFIG['price_row'], col=1
    )

    fig.add_trace(
        go.Scatter(
            x=datos['fecha'],
            y=datos['SMA_60'],
            name='SMA 60',
            line=dict(color='orange', width=1)
        ),
        row=CHART_CONFIG['price_row'], col=1
    )


def _agregar_volumen(fig: go.Figure, datos: pd.DataFrame):
    """Agrega gráfico de barras de volumen."""
    fig.add_trace(
        go.Bar(
            x=datos['fecha'],
            y=datos['volumen'],
            name='Volumen'
        ),
        row=CHART_CONFIG['volume_row'], col=1
    )


def _agregar_rsi(fig: go.Figure, datos: pd.DataFrame):
    """Agrega indicador RSI con líneas de referencia."""
    fig.add_trace(
        go.Scatter(
            x=datos['fecha'],
            y=datos['RSI'],
            name='RSI',
            line=dict(color='purple')
        ),
        row=CHART_CONFIG['rsi_row'], col=1
    )

    # Líneas de referencia
    fig.add_hline(
        y=RSI_OVERBOUGHT,
        line_dash="dash",
        line_color="red",
        row=CHART_CONFIG['rsi_row'], col=1
    )
    fig.add_hline(
        y=RSI_OVERSOLD,
        line_dash="dash",
        line_color="green",
        row=CHART_CONFIG['rsi_row'], col=1
    )


def _agregar_williams_r(fig: go.Figure, datos: pd.DataFrame):
    """Agrega indicador Williams %R con líneas de referencia."""
    fig.add_trace(
        go.Scatter(
            x=datos['fecha'],
            y=datos['WILLR'],
            name='Williams %R',
            line=dict(color='teal')
        ),
        row=CHART_CONFIG['willr_row'], col=1
    )

    # Líneas de referencia
    fig.add_hline(
        y=WILLR_OVERBOUGHT,
        line_dash="dash",
        line_color="red",
        row=CHART_CONFIG['willr_row'], col=1
    )
    fig.add_hline(
        y=WILLR_OVERSOLD,
        line_dash="dash",
        line_color="green",
        row=CHART_CONFIG['willr_row'], col=1
    )


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

        # Crear estructura base
        fig = _crear_estructura_grafico(ticker)
        logger.debug("Estructura base del gráfico creada")

        # Agregar componentes del gráfico
        _agregar_candlestick(fig, datos_historicos)
        logger.debug("Candlestick agregado")

        _agregar_medias_moviles(fig, datos_historicos)
        logger.debug("Medias móviles agregadas")

        _agregar_volumen(fig, datos_historicos)
        logger.debug("Volumen agregado")

        _agregar_rsi(fig, datos_historicos)
        logger.debug("RSI agregado")

        _agregar_williams_r(fig, datos_historicos)
        logger.debug("Williams %R agregado")

        # Configurar layout final
        fig.update_layout(
            title_text=f"Análisis Técnico para {ticker}",
            xaxis_rangeslider_visible=False,
            height=CHART_HEIGHT
        )
        logger.debug("Layout del gráfico configurado")

        # Guardar archivo HTML
        output_path = os.path.join(output_dir, f"{ticker}_analisis.html")
        fig.write_html(output_path)
        logger.info(f"Gráfico generado exitosamente: {output_path}")

    except Exception as e:
        logger.error(f"Error generando gráfico para {ticker}: {e}", exc_info=True)
        raise
