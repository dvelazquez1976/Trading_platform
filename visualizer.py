import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def generar_grafico(datos_historicos, resultado_analisis, ticker):
    """
    Genera un gráfico interactivo con los datos históricos y los resultados del análisis.

    Args:
        datos_historicos (pd.DataFrame): DataFrame con los datos de precios.
        resultado_analisis (dict): Diccionario con los resultados del análisis.
        ticker (str): El ticker de la acción.
    """
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=(f'{ticker} Candlestick', 'Volume', 'RSI', 'Williams %R'),
        row_heights=[0.6, 0.1, 0.15, 0.15]
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=datos_historicos['fecha'],
            open=datos_historicos['apertura'],
            high=datos_historicos['maximo'],
            low=datos_historicos['minimo'],
            close=datos_historicos['cierre'],
            name='Candlestick'
        ),
        row=1, col=1
    )

    # Moving Averages
    fig.add_trace(go.Scatter(x=datos_historicos['fecha'], y=datos_historicos['SMA_30'], name='SMA 30', line=dict(color='blue', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=datos_historicos['fecha'], y=datos_historicos['SMA_60'], name='SMA 60', line=dict(color='orange', width=1)), row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=datos_historicos['fecha'], y=datos_historicos['volumen'], name='Volume'), row=2, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=datos_historicos['fecha'], y=datos_historicos['RSI_14'], name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    # Williams %R
    fig.add_trace(go.Scatter(x=datos_historicos['fecha'], y=datos_historicos['WILLR_14'], name='Williams %R'), row=4, col=1)
    fig.add_hline(y=-20, line_dash="dash", line_color="red", row=4, col=1)
    fig.add_hline(y=-80, line_dash="dash", line_color="green", row=4, col=1)

    fig.update_layout(
        title_text=f"Análisis Técnico para {ticker}",
        xaxis_rangeslider_visible=False,
        height=800
    )

    fig.write_html(f"c:\\Python\\Plataforma_Trading\\salidas\\{ticker}_analisis.html")
