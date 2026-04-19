"""Indicadores técnicos básicos con pandas_ta."""

import pandas as pd
import pandas_ta as ta

from trading_platform.core.config import config_manager
from trading_platform.core.utils import rename_columns_to_english, rename_columns_to_spanish, validate_required_columns
from trading_platform.core.constants import STANDARD_COLUMNS
from trading_platform.core.logging import get_logger

logger = get_logger(__name__)


def calcular_indicadores(datos: pd.DataFrame) -> pd.DataFrame:
    """Calcula indicadores técnicos y los añade al DataFrame."""
    logger.info(f"Calculando indicadores para {len(datos)} registros")
    validate_required_columns(datos, STANDARD_COLUMNS['SPANISH'])

    df = rename_columns_to_english(datos)
    params = config_manager.get_indicator_params()

    _calcular_tendencia(df, params)
    _calcular_momentum(df, params)
    _calcular_volatilidad(df, params)
    _calcular_volumen_ind(df, params)

    advanced_cfg = config_manager.get('advanced_indicators', default={})
    if advanced_cfg.get('enabled', False):
        from trading_platform.indicators.advanced import calculate_all_advanced_indicators
        df = calculate_all_advanced_indicators(df)

    df = rename_columns_to_spanish(df)
    logger.info(f"Indicadores calculados: {len(df.columns) - len(STANDARD_COLUMNS['SPANISH'])} columnas añadidas")
    return df


def _calcular_tendencia(df: pd.DataFrame, params: dict):
    for period in params.get('sma_periods', [30, 60, 90]):
        df[f'SMA_{period}'] = ta.sma(df['close'], length=period)

    macd = ta.macd(df['close'], **params.get('macd_params', {"fast": 12, "slow": 26, "signal": 9}))
    if macd is not None:
        df['MACD']  = macd.iloc[:, 0]
        df['MACDh'] = macd.iloc[:, 1]
        df['MACDs'] = macd.iloc[:, 2]

    adx = ta.adx(df['high'], df['low'], df['close'], length=params.get('adx_period', 14))
    if adx is not None:
        df['ADX'] = adx.iloc[:, 0]
        df['DMP'] = adx.iloc[:, 2]
        df['DMN'] = adx.iloc[:, 3]


def _calcular_momentum(df: pd.DataFrame, params: dict):
    df['RSI']   = ta.rsi(df['close'], length=params.get('rsi_period', 14))

    stoch = ta.stoch(df['high'], df['low'], df['close'], **params.get('stoch_params', {"k": 14, "d": 3}))
    if stoch is not None:
        df['STOCHk'] = stoch.iloc[:, 0]
        df['STOCHd'] = stoch.iloc[:, 1]

    df['CCI']   = ta.cci(df['high'], df['low'], df['close'], length=params.get('cci_period', 20))
    df['WILLR'] = ta.willr(df['high'], df['low'], df['close'], length=params.get('willr_period', 14))
    df['AO']    = ta.ao(df['high'], df['low'], **params.get('ao_params', {"fast": 5, "slow": 34}))
    df['ROC']   = ta.roc(df['close'], length=params.get('roc_period', 12))


def _calcular_volatilidad(df: pd.DataFrame, params: dict):
    bb = ta.bbands(df['close'], **params.get('bollinger_params', {"length": 20, "std": 2}))
    if bb is not None:
        df['BBL_BB'] = bb.iloc[:, 0]
        df['BBM_BB'] = bb.iloc[:, 1]
        df['BBU_BB'] = bb.iloc[:, 2]


def _calcular_volumen_ind(df: pd.DataFrame, params: dict):
    df['MFI'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=params.get('mfi_period', 14))
