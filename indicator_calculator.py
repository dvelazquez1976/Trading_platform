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
    # Create a copy of the DataFrame and rename columns for pandas_ta compatibility
    df_ta = datos.copy()
    df_ta.rename(columns={
        'apertura': 'open',
        'maximo': 'high',
        'minimo': 'low',
        'cierre': 'close',
        'volumen': 'volume'
    }, inplace=True)

    # Create a Strategy
    MyStrategy = ta.Strategy(
        name="MyStrategy",
        description="My custom strategy",
        ta=[
            {"kind": "sma", "length": 30},
            {"kind": "sma", "length": 60},
            {"kind": "sma", "length": 90},
            {"kind": "rsi", "length": 14},
            {"kind": "stoch", "k": 14, "d": 3},
            {"kind": "macd", "fast": 12, "slow": 26, "signal": 9},
            {"kind": "bbands", "length": 20, "std": 2},
            {"kind": "cci", "length": 20},
            {"kind": "adx", "length": 14},
            {"kind": "mfi", "length": 14},
            {"kind": "willr", "length": 14},
            {"kind": "ao", "fast": 5, "slow": 34},
            {"kind": "roc", "length": 12},
        ]
    )

    # Run the strategy
    df_ta.ta.strategy(MyStrategy)

    # Rename columns to match the original names
    df_ta.rename(columns={
        'open': 'apertura',
        'high': 'maximo',
        'low': 'minimo',
        'close': 'cierre',
        'volume': 'volumen'
    }, inplace=True)

    return df_ta
