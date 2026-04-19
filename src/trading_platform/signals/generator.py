"""Generador de señales de trading basadas en indicadores técnicos."""

import pandas as pd
from typing import Dict, Tuple

from trading_platform.core.config import config_manager
from trading_platform.core.logging import get_logger

logger = get_logger(__name__)

SIGNAL_BUY  = "COMPRA"
SIGNAL_SELL = "VENTA"
SIGNAL_HOLD = "KEEP/NO SIGNAL"


def generar_senales(datos: pd.DataFrame) -> Dict:
    ticker = datos.iloc[-1]['ticker'] if 'ticker' in datos.columns else 'Unknown'
    thresholds = config_manager.get_signal_thresholds()
    senales = _inicializar_senales()
    ultimo, anterior = datos.iloc[-1], datos.iloc[-2]

    # 1. Cruce de medias
    senales["Cruce_Medias"] = _cruce(
        ultimo['SMA_30'], ultimo['SMA_60'], anterior['SMA_30'], anterior['SMA_60'])

    # 2. RSI
    senales["RSI"] = _umbral(ultimo['RSI'], thresholds.get('rsi_oversold', 30), thresholds.get('rsi_overbought', 70))

    # 3. Estocástico
    so, sob = thresholds.get('stoch_oversold', 20), thresholds.get('stoch_overbought', 80)
    if ultimo['STOCHk'] < so and ultimo['STOCHd'] < so:
        senales["Estocastico"] = _cruce(ultimo['STOCHk'], ultimo['STOCHd'], anterior['STOCHk'], anterior['STOCHd'])
    elif ultimo['STOCHk'] > sob and ultimo['STOCHd'] > sob:
        c = _cruce(ultimo['STOCHk'], ultimo['STOCHd'], anterior['STOCHk'], anterior['STOCHd'])
        if c == SIGNAL_BUY:   senales["Estocastico"] = SIGNAL_SELL
        elif c == SIGNAL_SELL: senales["Estocastico"] = SIGNAL_BUY

    # 4. MACD — usa nombres estandarizados (fix bug original)
    senales["MACD"] = _cruce(ultimo['MACD'], ultimo['MACDs'], anterior['MACD'], anterior['MACDs'])

    # 5. Bandas Bollinger
    if ultimo['cierre'] < ultimo['BBL_BB']:   senales["Bandas_Bollinger"] = SIGNAL_BUY
    elif ultimo['cierre'] > ultimo['BBU_BB']: senales["Bandas_Bollinger"] = SIGNAL_SELL

    # 6. Williams %R
    senales["Williams_R"] = _umbral(
        ultimo['WILLR'], thresholds.get('willr_oversold', -80), thresholds.get('willr_overbought', -20))

    # 7. Awesome Oscillator
    senales["Awesome_Oscillator"] = _cruce(ultimo['AO'], 0, anterior['AO'], 0)

    # 8. ROC
    roc_b, roc_s = thresholds.get('roc_bullish', 5), thresholds.get('roc_bearish', -5)
    if ultimo['ROC'] > roc_b:   senales["ROC"] = SIGNAL_BUY
    elif ultimo['ROC'] < roc_s: senales["ROC"] = SIGNAL_SELL

    # Señales avanzadas
    from trading_platform.signals.advanced import generate_advanced_signals
    senales.update(generate_advanced_signals(datos))

    resumen = _resumen(senales)
    buys = list(senales.values()).count(SIGNAL_BUY)
    sells = list(senales.values()).count(SIGNAL_SELL)
    logger.info(f"{ticker}: {buys} COMPRA, {sells} VENTA → {resumen}")

    return {
        "ticker": ticker,
        "fecha": ultimo['fecha'].strftime('%Y-%m-%d'),
        "precio_cierre": ultimo['cierre'],
        "señales": senales,
        "resumen": resumen
    }


def _inicializar_senales() -> Dict:
    return {k: SIGNAL_HOLD for k in [
        "Cruce_Medias", "RSI", "Estocastico", "MACD",
        "Bandas_Bollinger", "Williams_R", "Awesome_Oscillator", "ROC"
    ]}


def _cruce(val, ref, val_ant, ref_ant) -> str:
    if val > ref and val_ant <= ref_ant:  return SIGNAL_BUY
    if val < ref and val_ant >= ref_ant:  return SIGNAL_SELL
    return SIGNAL_HOLD


def _umbral(val, low, high) -> str:
    if val < low:  return SIGNAL_BUY
    if val > high: return SIGNAL_SELL
    return SIGNAL_HOLD


def _resumen(senales: Dict) -> str:
    vals = list(senales.values())
    b, s = vals.count(SIGNAL_BUY), vals.count(SIGNAL_SELL)
    if b > s:   return "COMPRA"
    if s > b:   return "VENTA"
    return "KEEP"
