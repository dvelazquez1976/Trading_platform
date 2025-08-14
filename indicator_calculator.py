import pandas as pd
import pandas_ta as ta

def calcular_indicadores(datos):
    """
    Calcula una serie de indicadores técnicos y los añade al DataFrame.

    Args:
        datos (pd.DataFrame): DataFrame con los datos de precios.

    Returns:
        pd.DataFrame: DataFrame con los indicadores calculados.
    """
    datos.ta.sma(close=datos['cierre'], length=30, append=True)
    datos.ta.sma(close=datos['cierre'], length=60, append=True)
    datos.ta.sma(close=datos['cierre'], length=90, append=True)

    # RSI (Índice de Fuerza Relativa)
    datos.ta.rsi(close=datos['cierre'], length=14, append=True)

    # Estocástico (Stochastic Oscillator)
    datos.ta.stoch(high=datos['maximo'], low=datos['minimo'], close=datos['cierre'], k=14, d=3, append=True)

    # MACD (Moving Average Convergence Divergence)
    datos.ta.macd(close=datos['cierre'], fast=12, slow=26, signal=9, append=True)

    # Bandas de Bollinger (Bollinger Bands)
    bbands = datos.ta.bbands(close=datos['cierre'], length=20, std=2)
    datos['BBL_20_2'] = bbands['BBL_20_2']
    datos['BBM_20_2'] = bbands['BBM_20_2']
    datos['BBU_20_2'] = bbands['BBU_20_2']

    # CCI (Commodity Channel Index)
    datos.ta.cci(close=datos['cierre'], length=20, append=True)

    # ADX (Average Directional Movement Index)
    datos.ta.adx(high=datos['maximo'], low=datos['minimo'], close=datos['cierre'], length=14, append=True)

    # MFI (Money Flow Index) - Requires 'volume' column
    # Assuming 'volumen' column exists in the DataFrame
    datos.ta.mfi(high=datos['maximo'], low=datos['minimo'], close=datos['cierre'], volume=datos['volumen'], length=14, append=True)
    
    return datos
