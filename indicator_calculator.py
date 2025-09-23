import pandas as pd
import pandas_ta as ta
from config_manager import config_manager
from utils import rename_columns_to_english, rename_columns_to_spanish, validate_required_columns
from constants import STANDARD_COLUMNS
from advanced_indicators import calculate_all_advanced_indicators

def calcular_indicadores(datos):
    """
    Calcula una serie de indicadores técnicos y los añade al DataFrame.

    Args:
        datos (pd.DataFrame): DataFrame con los datos de precios.

    Returns:
        pd.DataFrame: DataFrame con los indicadores calculados.
    """
    # Validar columnas requeridas
    validate_required_columns(datos, STANDARD_COLUMNS['SPANISH'])

    # Crear copia y renombrar columnas para compatibilidad con pandas_ta
    df_ta = rename_columns_to_english(datos)

    # Obtener parámetros de configuración
    params = config_manager.get_indicator_params()

    # Crear estrategias basadas en configuración
    strategy_indicators = []

    # SMAs
    for period in params.get('sma_periods', [30, 60, 90]):
        strategy_indicators.append({"kind": "sma", "length": period})

    # Otros indicadores
    strategy_indicators.extend([
        {"kind": "rsi", "length": params.get('rsi_period', 14)},
        {"kind": "stoch", **params.get('stoch_params', {"k": 14, "d": 3})},
        {"kind": "macd", **params.get('macd_params', {"fast": 12, "slow": 26, "signal": 9})},
        {"kind": "bbands", **params.get('bollinger_params', {"length": 20, "std": 2})},
        {"kind": "cci", "length": params.get('cci_period', 20)},
        {"kind": "adx", "length": params.get('adx_period', 14)},
        {"kind": "mfi", "length": params.get('mfi_period', 14)},
        {"kind": "willr", "length": params.get('willr_period', 14)},
        {"kind": "ao", **params.get('ao_params', {"fast": 5, "slow": 34})},
        {"kind": "roc", "length": params.get('roc_period', 12)},
    ])

    # Create a Strategy
    MyStrategy = ta.Strategy(
        name="MyStrategy",
        description="My custom strategy",
        ta=strategy_indicators
    )

    # Run the strategy
    df_ta.ta.strategy(MyStrategy)

    # Calcular indicadores avanzados si están habilitados
    advanced_config = config_manager.get('advanced_indicators', default={})
    if advanced_config.get('enabled', False):
        print("Calculando indicadores avanzados...")
        df_ta = calculate_all_advanced_indicators(df_ta)

    # Renombrar columnas de vuelta al español
    df_ta = rename_columns_to_spanish(df_ta)

    return df_ta
