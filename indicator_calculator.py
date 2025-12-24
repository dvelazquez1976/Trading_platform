import pandas as pd
import pandas_ta as ta
from config_manager import config_manager
from utils import rename_columns_to_english, rename_columns_to_spanish, validate_required_columns
from constants import STANDARD_COLUMNS
from advanced_indicators import calculate_all_advanced_indicators
from logger_config import get_logger

logger = get_logger(__name__)

def calcular_indicadores(datos: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula una serie de indicadores técnicos y los añade al DataFrame.
    
    El proceso incluye:
    1. Validación de columnas requeridas.
    2. Conversión de nombres de columnas al inglés (para compatibilidad con pandas_ta).
    3. Cálculo de indicadores de tendencia (SMA, MACD, ADX).
    4. Cálculo de indicadores de momentum (RSI, Stoch, CCI, Williams %R, AO, ROC).
    5. Cálculo de indicadores de volatilidad (Bollinger Bands).
    6. Cálculo de indicadores de volumen (MFI).
    7. Cálculo de indicadores avanzados (opcional).
    8. Reconversión de nombres al español.

    Args:
        datos (pd.DataFrame): DataFrame con columnas [fecha, apertura, maximo, minimo, cierre, volumen].

    Returns:
        pd.DataFrame: DataFrame original enriquecido con columnas de indicadores.
    """
    logger.info(f"Iniciando cálculo de indicadores técnicos para {len(datos)} registros")

    # Validar columnas requeridas
    validate_required_columns(datos, STANDARD_COLUMNS['SPANISH'])
    
    # Crear copia y renombrar columnas para compatibilidad con pandas_ta
    df_ta = rename_columns_to_english(datos)

    # Obtener parámetros de configuración
    params = config_manager.get_indicator_params()

    # --- 1. INDICADORES DE TENDENCIA ---
    _calcular_tendencia(df_ta, params)

    # --- 2. INDICADORES DE MOMENTUM ---
    _calcular_momentum(df_ta, params)

    # --- 3. INDICADORES DE VOLATILIDAD ---
    _calcular_volatilidad(df_ta, params)

    # --- 4. INDICADORES DE VOLUMEN ---
    _calcular_volumen_ind(df_ta, params)

    # --- 5. INDICADORES AVANZADOS (Opcional) ---
    advanced_config = config_manager.get('advanced_indicators', default={})
    if advanced_config.get('enabled', False):
        logger.info("Calculando indicadores avanzados...")
        df_ta = calculate_all_advanced_indicators(df_ta)

    # Renombrar columnas de vuelta al español
    df_ta = rename_columns_to_spanish(df_ta)
    
    total_indicators = len(df_ta.columns) - len(STANDARD_COLUMNS['SPANISH'])
    logger.info(f"Cálculo completado: {total_indicators} indicadores añadidos")

    return df_ta

def _calcular_tendencia(df: pd.DataFrame, params: dict):
    """Calcula indicadores de tendencia: SMA, MACD, ADX."""
    # SMAs
    sma_periods = params.get('sma_periods', [30, 60, 90])
    for period in sma_periods:
        df[f'SMA_{period}'] = ta.sma(df['close'], length=period)
    
    # MACD
    macd_params = params.get('macd_params', {"fast": 12, "slow": 26, "signal": 9})
    macd = ta.macd(df['close'], **macd_params)
    if macd is not None:
        # Standardize names: MACD, MACDh (histogram), MACDs (signal)
        df['MACD'] = macd.iloc[:, 0]
        df['MACDh'] = macd.iloc[:, 1]
        df['MACDs'] = macd.iloc[:, 2]

    # ADX
    adx = ta.adx(df['high'], df['low'], df['close'], length=params.get('adx_period', 14))
    if adx is not None:
        # Standardize names: ADX, DMP (+DI), DMN (-DI)
        df['ADX'] = adx.iloc[:, 0]
        df['DMP'] = adx.iloc[:, 2]
        df['DMN'] = adx.iloc[:, 3]

def _calcular_momentum(df: pd.DataFrame, params: dict):
    """Calcula indicadores de momentum: RSI, Stochastic, CCI, Williams %R, AO, ROC."""
    # RSI
    df['RSI'] = ta.rsi(df['close'], length=params.get('rsi_period', 14))

    # Stochastic
    stoch_params = params.get('stoch_params', {"k": 14, "d": 3})
    stoch = ta.stoch(df['high'], df['low'], df['close'], **stoch_params)
    if stoch is not None:
        # Standardize names: STOCHk, STOCHd
        df['STOCHk'] = stoch.iloc[:, 0]
        df['STOCHd'] = stoch.iloc[:, 1]

    # CCI
    df['CCI'] = ta.cci(df['high'], df['low'], df['close'], length=params.get('cci_period', 20))

    # Williams %R
    df['WILLR'] = ta.willr(df['high'], df['low'], df['close'], length=params.get('willr_period', 14))

    # Awesome Oscillator
    ao_params = params.get('ao_params', {"fast": 5, "slow": 34})
    df['AO'] = ta.ao(df['high'], df['low'], **ao_params)

    # Rate of Change
    df['ROC'] = ta.roc(df['close'], length=params.get('roc_period', 12))

def _calcular_volatilidad(df: pd.DataFrame, params: dict):
    """Calcula indicadores de volatilidad: Bollinger Bands."""
    bb_params = params.get('bollinger_params', {"length": 20, "std": 2})
    bb = ta.bbands(df['close'], **bb_params)
    if bb is not None:
        # Standardize names: BBL (lower), BBM (middle), BBU (upper)
        df['BBL_BB'] = bb.iloc[:, 0]
        df['BBM_BB'] = bb.iloc[:, 1]
        df['BBU_BB'] = bb.iloc[:, 2]

def _calcular_volumen_ind(df: pd.DataFrame, params: dict):
    """Calcula indicadores de volumen: MFI."""
    df['MFI'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=params.get('mfi_period', 14))
