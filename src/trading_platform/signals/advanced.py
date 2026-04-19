"""Señales para indicadores técnicos avanzados."""

import pandas as pd
from typing import Dict, Any

from trading_platform.core.config import config_manager

SIGNAL_BUY  = "COMPRA"
SIGNAL_SELL = "VENTA"
SIGNAL_HOLD = "KEEP/NO SIGNAL"


def generate_advanced_signals(datos: pd.DataFrame) -> Dict[str, str]:
    if len(datos) < 2:
        return {}
    cfg = config_manager.get('advanced_indicators', default={})
    if not cfg.get('enabled', False):
        return {}

    thr = config_manager.get('advanced_signals', default={})
    ultimo, anterior = datos.iloc[-1], datos.iloc[-2]
    senales = {}

    try:
        _stoch_rsi(senales, ultimo, anterior, thr)
        _tsi(senales, ultimo, thr)
        _uo(senales, ultimo, thr)
        _chaikin(senales, ultimo, anterior, thr)
        _aroon(senales, ultimo, thr)
        _trix(senales, ultimo, anterior, thr)
        _volume_rsi(senales, ultimo, thr)
        _dpo(senales, ultimo, anterior, thr)
    except Exception as e:
        print(f"Error señales avanzadas: {e}")

    return senales


def get_advanced_indicator_values(datos: pd.DataFrame) -> Dict[str, Any]:
    if datos.empty:
        return {}
    cfg = config_manager.get('advanced_indicators', default={})
    if not cfg.get('enabled', False):
        return {}
    ultimo = datos.iloc[-1]
    cols = ['STOCHRSI_K', 'TSI', 'UO', 'CHAIKIN_OSC', 'AROONOSC', 'TRIX', 'VOLRSI', 'DPO']
    return {c: ultimo[c] for c in cols if c in ultimo.index}


# ── Signal helpers ─────────────────────────────────────────────────────────

def _stoch_rsi(s, u, a, t):
    if 'STOCHRSI_K' not in u.index: return
    ov, ob = t.get('stoch_rsi_oversold', 20), t.get('stoch_rsi_overbought', 80)
    if u['STOCHRSI_K'] < ov and u['STOCHRSI_K'] > u['STOCHRSI_D'] and a['STOCHRSI_K'] <= a['STOCHRSI_D']:
        s["Stochastic_RSI"] = SIGNAL_BUY
    elif u['STOCHRSI_K'] > ob and u['STOCHRSI_K'] < u['STOCHRSI_D'] and a['STOCHRSI_K'] >= a['STOCHRSI_D']:
        s["Stochastic_RSI"] = SIGNAL_SELL
    else:
        s["Stochastic_RSI"] = SIGNAL_HOLD

def _tsi(s, u, t):
    if 'TSI' not in u.index: return
    b, sell = t.get('tsi_bullish', 5), t.get('tsi_bearish', -5)
    s["TSI"] = SIGNAL_BUY if u['TSI'] > b else (SIGNAL_SELL if u['TSI'] < sell else SIGNAL_HOLD)

def _uo(s, u, t):
    if 'UO' not in u.index: return
    ov, ob = t.get('uo_oversold', 30), t.get('uo_overbought', 70)
    s["Ultimate_Oscillator"] = SIGNAL_BUY if u['UO'] < ov else (SIGNAL_SELL if u['UO'] > ob else SIGNAL_HOLD)

def _chaikin(s, u, a, t):
    if 'CHAIKIN_OSC' not in u.index: return
    th = t.get('chaikin_bullish', 0)
    if u['CHAIKIN_OSC'] > th and a['CHAIKIN_OSC'] <= th:   s["Chaikin_Oscillator"] = SIGNAL_BUY
    elif u['CHAIKIN_OSC'] < th and a['CHAIKIN_OSC'] >= th: s["Chaikin_Oscillator"] = SIGNAL_SELL
    else:                                                    s["Chaikin_Oscillator"] = SIGNAL_HOLD

def _aroon(s, u, t):
    if 'AROONOSC' not in u.index: return
    b, sell = t.get('aroon_osc_bullish', 50), t.get('aroon_osc_bearish', -50)
    s["Aroon_Oscillator"] = SIGNAL_BUY if u['AROONOSC'] > b else (SIGNAL_SELL if u['AROONOSC'] < sell else SIGNAL_HOLD)

def _trix(s, u, a, t):
    if 'TRIX' not in u.index: return
    th = t.get('trix_bullish', 0)
    if u['TRIX'] > th and a['TRIX'] <= th:   s["TRIX"] = SIGNAL_BUY
    elif u['TRIX'] < th and a['TRIX'] >= th: s["TRIX"] = SIGNAL_SELL
    else:                                      s["TRIX"] = SIGNAL_HOLD

def _volume_rsi(s, u, t):
    if 'VOLRSI' not in u.index: return
    ov, ob = t.get('volume_rsi_oversold', 30), t.get('volume_rsi_overbought', 70)
    s["Volume_RSI"] = SIGNAL_BUY if u['VOLRSI'] < ov else (SIGNAL_SELL if u['VOLRSI'] > ob else SIGNAL_HOLD)

def _dpo(s, u, a, t):
    if 'DPO' not in u.index: return
    th = t.get('dpo_bullish', 0)
    if u['DPO'] > th and a['DPO'] <= th:   s["DPO"] = SIGNAL_BUY
    elif u['DPO'] < th and a['DPO'] >= th: s["DPO"] = SIGNAL_SELL
    else:                                    s["DPO"] = SIGNAL_HOLD
