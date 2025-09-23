"""Indicadores técnicos avanzados para análisis de trading."""

import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Dict, Any
from config_manager import config_manager

def calculate_stochastic_rsi(df: pd.DataFrame, rsi_period: int = 14, stoch_period: int = 14) -> pd.DataFrame:
    """
    Calcula el Stochastic RSI - combina RSI con Estocástico para mejor timing.

    Args:
        df: DataFrame con datos OHLCV
        rsi_period: Período para RSI
        stoch_period: Período para Estocástico

    Returns:
        DataFrame con Stochastic RSI añadido
    """
    result_df = df.copy()

    # Calcular RSI
    rsi = ta.rsi(df['close'], length=rsi_period)

    # Aplicar Estocástico al RSI
    stoch_rsi = ta.stoch(high=rsi, low=rsi, close=rsi, k=stoch_period)

    # Añadir al DataFrame
    result_df[f'STOCHRSI_K_{rsi_period}_{stoch_period}'] = stoch_rsi[f'STOCHk_{stoch_period}_3_3']
    result_df[f'STOCHRSI_D_{rsi_period}_{stoch_period}'] = stoch_rsi[f'STOCHd_{stoch_period}_3_3']

    return result_df

def calculate_tsi(df: pd.DataFrame, long_period: int = 25, short_period: int = 13) -> pd.DataFrame:
    """
    Calcula el True Strength Index (TSI) - oscilador suavizado que reduce ruido.

    Args:
        df: DataFrame con datos OHLCV
        long_period: Período largo para suavizado
        short_period: Período corto para suavizado

    Returns:
        DataFrame con TSI añadido
    """
    result_df = df.copy()

    # TSI no está directamente en pandas_ta, lo calculamos manualmente
    price_changes = df['close'].diff()

    # Doble suavizado de los cambios de precio
    first_smooth = price_changes.ewm(span=long_period).mean()
    double_smooth = first_smooth.ewm(span=short_period).mean()

    # Doble suavizado de los valores absolutos
    abs_changes = price_changes.abs()
    first_smooth_abs = abs_changes.ewm(span=long_period).mean()
    double_smooth_abs = first_smooth_abs.ewm(span=short_period).mean()

    # Calcular TSI
    tsi = 100 * (double_smooth / double_smooth_abs)

    result_df[f'TSI_{long_period}_{short_period}'] = tsi

    return result_df

def calculate_ultimate_oscillator(df: pd.DataFrame, period1: int = 7, period2: int = 14, period3: int = 28) -> pd.DataFrame:
    """
    Calcula el Ultimate Oscillator - combina múltiples timeframes.

    Args:
        df: DataFrame con datos OHLCV
        period1: Período corto
        period2: Período medio
        period3: Período largo

    Returns:
        DataFrame con Ultimate Oscillator añadido
    """
    result_df = df.copy()

    # Ultimate Oscillator está disponible en pandas_ta
    uo = ta.uo(high=df['high'], low=df['low'], close=df['close'],
               fast=period1, medium=period2, slow=period3)

    result_df[f'UO_{period1}_{period2}_{period3}'] = uo

    return result_df

def calculate_chaikin_oscillator(df: pd.DataFrame, fast_period: int = 3, slow_period: int = 10) -> pd.DataFrame:
    """
    Calcula el Chaikin Oscillator - detecta divergencias entre precio y volumen.

    Args:
        df: DataFrame con datos OHLCV
        fast_period: Período rápido
        slow_period: Período lento

    Returns:
        DataFrame con Chaikin Oscillator añadido
    """
    result_df = df.copy()

    # Primero calcular Accumulation/Distribution Line
    ad = ta.ad(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'])

    # Calcular medias móviles de A/D
    fast_ema = ad.ewm(span=fast_period).mean()
    slow_ema = ad.ewm(span=slow_period).mean()

    # Chaikin Oscillator = Fast EMA - Slow EMA
    chaikin_osc = fast_ema - slow_ema

    result_df[f'CHAIKIN_OSC_{fast_period}_{slow_period}'] = chaikin_osc

    return result_df

def calculate_aroon_oscillator(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calcula el Aroon Oscillator - identifica tendencias emergentes.

    Args:
        df: DataFrame con datos OHLCV
        period: Período de cálculo

    Returns:
        DataFrame con Aroon Oscillator añadido
    """
    result_df = df.copy()

    # Aroon está disponible en pandas_ta
    aroon = ta.aroon(high=df['high'], low=df['low'], length=period)

    # Aroon Oscillator = Aroon Up - Aroon Down
    result_df[f'AROONU_{period}'] = aroon[f'AROONU_{period}']
    result_df[f'AROOND_{period}'] = aroon[f'AROOND_{period}']
    result_df[f'AROONOSC_{period}'] = aroon[f'AROONU_{period}'] - aroon[f'AROOND_{period}']

    return result_df

def calculate_trix(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calcula TRIX - Triple EMA suavizada para filtrar ruido.

    Args:
        df: DataFrame con datos OHLCV
        period: Período de cálculo

    Returns:
        DataFrame con TRIX añadido
    """
    result_df = df.copy()

    # TRIX está disponible en pandas_ta
    trix = ta.trix(close=df['close'], length=period)

    result_df[f'TRIX_{period}'] = trix

    return result_df

def calculate_volume_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calcula Volume RSI - RSI aplicado al volumen.

    Args:
        df: DataFrame con datos OHLCV
        period: Período de cálculo

    Returns:
        DataFrame con Volume RSI añadido
    """
    result_df = df.copy()

    # Aplicar RSI al volumen
    volume_rsi = ta.rsi(df['volume'], length=period)

    result_df[f'VOLRSI_{period}'] = volume_rsi

    return result_df

def calculate_dpo(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    Calcula Detrended Price Oscillator - elimina tendencia para ver ciclos.

    Args:
        df: DataFrame con datos OHLCV
        period: Período de cálculo

    Returns:
        DataFrame con DPO añadido
    """
    result_df = df.copy()

    # DPO = Close - SMA[n/2 + 1] periods ago
    sma = df['close'].rolling(window=period).mean()
    shift_periods = (period // 2) + 1
    dpo = df['close'] - sma.shift(shift_periods)

    result_df[f'DPO_{period}'] = dpo

    return result_df

def calculate_all_advanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula todos los indicadores avanzados.

    Args:
        df: DataFrame con datos OHLCV en inglés

    Returns:
        DataFrame con todos los indicadores avanzados
    """
    result_df = df.copy()

    try:
        # Obtener configuración para indicadores avanzados
        advanced_config = config_manager.get('advanced_indicators', default={})

        # Calcular cada indicador
        result_df = calculate_stochastic_rsi(
            result_df,
            rsi_period=advanced_config.get('stoch_rsi_rsi_period', 14),
            stoch_period=advanced_config.get('stoch_rsi_stoch_period', 14)
        )

        result_df = calculate_tsi(
            result_df,
            long_period=advanced_config.get('tsi_long_period', 25),
            short_period=advanced_config.get('tsi_short_period', 13)
        )

        result_df = calculate_ultimate_oscillator(
            result_df,
            period1=advanced_config.get('uo_period1', 7),
            period2=advanced_config.get('uo_period2', 14),
            period3=advanced_config.get('uo_period3', 28)
        )

        result_df = calculate_chaikin_oscillator(
            result_df,
            fast_period=advanced_config.get('chaikin_fast', 3),
            slow_period=advanced_config.get('chaikin_slow', 10)
        )

        result_df = calculate_aroon_oscillator(
            result_df,
            period=advanced_config.get('aroon_period', 14)
        )

        result_df = calculate_trix(
            result_df,
            period=advanced_config.get('trix_period', 14)
        )

        result_df = calculate_volume_rsi(
            result_df,
            period=advanced_config.get('volume_rsi_period', 14)
        )

        result_df = calculate_dpo(
            result_df,
            period=advanced_config.get('dpo_period', 20)
        )

        print("Indicadores avanzados calculados exitosamente.")

    except Exception as e:
        print(f"Error calculando indicadores avanzados: {e}")

    return result_df