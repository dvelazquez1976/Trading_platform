"""Indicadores técnicos avanzados (opcionales)."""

import pandas as pd
import pandas_ta as ta
import numpy as np

from trading_platform.core.config import config_manager


def calculate_all_advanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
    cfg = config_manager.get('advanced_indicators', default={})
    result = df.copy()
    try:
        result = _stoch_rsi(result, cfg.get('stoch_rsi_rsi_period', 14), cfg.get('stoch_rsi_stoch_period', 14))
        result = _tsi(result, cfg.get('tsi_long_period', 25), cfg.get('tsi_short_period', 13))
        result = _uo(result, cfg.get('uo_period1', 7), cfg.get('uo_period2', 14), cfg.get('uo_period3', 28))
        result = _chaikin(result, cfg.get('chaikin_fast', 3), cfg.get('chaikin_slow', 10))
        result = _aroon(result, cfg.get('aroon_period', 14))
        result = _trix(result, cfg.get('trix_period', 14))
        result = _volume_rsi(result, cfg.get('volume_rsi_period', 14))
        result = _dpo(result, cfg.get('dpo_period', 20))
    except Exception as e:
        print(f"Error en indicadores avanzados: {e}")
    return result


def _stoch_rsi(df, rsi_period, stoch_period):
    rsi = ta.rsi(df['close'], length=rsi_period)
    stoch = ta.stoch(high=rsi, low=rsi, close=rsi, k=stoch_period)
    if stoch is not None:
        df['STOCHRSI_K'] = stoch.iloc[:, 0]
        df['STOCHRSI_D'] = stoch.iloc[:, 1]
    return df

def _tsi(df, long, short):
    changes = df['close'].diff()
    ds = changes.ewm(span=long).mean().ewm(span=short).mean()
    ds_abs = changes.abs().ewm(span=long).mean().ewm(span=short).mean()
    df['TSI'] = 100 * (ds / ds_abs)
    return df

def _uo(df, p1, p2, p3):
    uo = ta.uo(high=df['high'], low=df['low'], close=df['close'], fast=p1, medium=p2, slow=p3)
    df['UO'] = uo
    return df

def _chaikin(df, fast, slow):
    ad = ta.ad(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'])
    df['CHAIKIN_OSC'] = ad.ewm(span=fast).mean() - ad.ewm(span=slow).mean()
    return df

def _aroon(df, period):
    aroon = ta.aroon(high=df['high'], low=df['low'], length=period)
    if aroon is not None:
        df['AROONOSC'] = aroon.iloc[:, 0] - aroon.iloc[:, 1]
    return df

def _trix(df, period):
    trix = ta.trix(close=df['close'], length=period)
    df['TRIX'] = trix.iloc[:, 0] if isinstance(trix, pd.DataFrame) else trix
    return df

def _volume_rsi(df, period):
    df['VOLRSI'] = ta.rsi(df['volume'], length=period)
    return df

def _dpo(df, period):
    sma = df['close'].rolling(window=period).mean()
    df['DPO'] = df['close'] - sma.shift((period // 2) + 1)
    return df
