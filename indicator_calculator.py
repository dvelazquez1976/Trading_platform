import pandas as pd
import pandas_ta as ta
from config_manager import config_manager
from utils import rename_columns_to_english, rename_columns_to_spanish, validate_required_columns
from constants import STANDARD_COLUMNS
from advanced_indicators import calculate_all_advanced_indicators
from logger_config import get_logger

logger = get_logger(__name__)

def calcular_indicadores(datos):
    """
    Calcula una serie de indicadores técnicos y los añade al DataFrame.

    Args:
        datos (pd.DataFrame): DataFrame con los datos de precios.

    Returns:
        pd.DataFrame: DataFrame con los indicadores calculados.
    """
    logger.info(f"Iniciando cálculo de indicadores técnicos para {len(datos)} registros")

    # Validar columnas requeridas
    validate_required_columns(datos, STANDARD_COLUMNS['SPANISH'])
    logger.debug("Validación de columnas completada")

    # Crear copia y renombrar columnas para compatibilidad con pandas_ta
    df_ta = rename_columns_to_english(datos)

    # Obtener parámetros de configuración
    params = config_manager.get_indicator_params()
    logger.debug(f"Parámetros de configuración cargados: {list(params.keys())}")

    # Calcular indicadores directamente
    logger.debug("Calculando indicadores básicos...")

    # SMAs
    sma_periods = params.get('sma_periods', [30, 60, 90])
    for period in sma_periods:
        df_ta[f'SMA_{period}'] = ta.sma(df_ta['close'], length=period)
    logger.debug(f"SMAs calculadas para períodos: {sma_periods}")

    # RSI
    df_ta['RSI'] = ta.rsi(df_ta['close'], length=params.get('rsi_period', 14))
    logger.debug("RSI calculado")

    # Stochastic
    stoch_params = params.get('stoch_params', {"k": 14, "d": 3})
    stoch = ta.stoch(df_ta['high'], df_ta['low'], df_ta['close'], **stoch_params)
    if stoch is not None:
        df_ta = pd.concat([df_ta, stoch], axis=1)
        logger.debug(f"Stochastic calculado (k={stoch_params['k']}, d={stoch_params['d']})")

    # MACD
    macd_params = params.get('macd_params', {"fast": 12, "slow": 26, "signal": 9})
    macd = ta.macd(df_ta['close'], **macd_params)
    if macd is not None:
        df_ta = pd.concat([df_ta, macd], axis=1)
        logger.debug(f"MACD calculado ({macd_params['fast']}, {macd_params['slow']}, {macd_params['signal']})")

    # Bollinger Bands
    bb_params = params.get('bollinger_params', {"length": 20, "std": 2})
    bb = ta.bbands(df_ta['close'], **bb_params)
    if bb is not None:
        df_ta = pd.concat([df_ta, bb], axis=1)
        logger.debug(f"Bandas de Bollinger calculadas (length={bb_params['length']}, std={bb_params['std']})")

    # CCI
    df_ta['CCI'] = ta.cci(df_ta['high'], df_ta['low'], df_ta['close'], length=params.get('cci_period', 20))
    logger.debug("CCI calculado")

    # ADX
    adx = ta.adx(df_ta['high'], df_ta['low'], df_ta['close'], length=params.get('adx_period', 14))
    if adx is not None:
        df_ta = pd.concat([df_ta, adx], axis=1)
        logger.debug("ADX calculado")

    # MFI
    df_ta['MFI'] = ta.mfi(df_ta['high'], df_ta['low'], df_ta['close'], df_ta['volume'], length=params.get('mfi_period', 14))
    logger.debug("MFI calculado")

    # Williams %R
    df_ta['WILLR'] = ta.willr(df_ta['high'], df_ta['low'], df_ta['close'], length=params.get('willr_period', 14))
    logger.debug("Williams %R calculado")

    # Awesome Oscillator
    ao_params = params.get('ao_params', {"fast": 5, "slow": 34})
    df_ta['AO'] = ta.ao(df_ta['high'], df_ta['low'], **ao_params)
    logger.debug("Awesome Oscillator calculado")

    # Rate of Change
    df_ta['ROC'] = ta.roc(df_ta['close'], length=params.get('roc_period', 12))
    logger.debug("ROC calculado")

    # Calcular indicadores avanzados si están habilitados
    advanced_config = config_manager.get('advanced_indicators', default={})
    if advanced_config.get('enabled', False):
        logger.info("Indicadores avanzados habilitados - iniciando cálculo...")
        df_ta = calculate_all_advanced_indicators(df_ta)
        logger.info("Indicadores avanzados calculados exitosamente")

    # Renombrar columnas de vuelta al español
    df_ta = rename_columns_to_spanish(df_ta)
    logger.debug("Columnas renombradas de vuelta al español")

    total_indicators = len(df_ta.columns) - len(STANDARD_COLUMNS['SPANISH'])
    logger.info(f"Cálculo de indicadores completado: {total_indicators} indicadores añadidos")

    return df_ta
