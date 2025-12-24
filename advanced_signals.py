"""Generador de señales para indicadores avanzados."""

import pandas as pd
from typing import Dict, Any
from config_manager import config_manager

def generate_advanced_signals(datos: pd.DataFrame) -> Dict[str, str]:
    """
    Genera señales de trading basadas en indicadores avanzados.

    Args:
        datos: DataFrame con datos y indicadores calculados

    Returns:
        Diccionario con señales de cada indicador avanzado
    """
    if len(datos) < 2:
        return {}

    # Obtener umbrales de configuración
    thresholds = config_manager.get('advanced_signals', default={})
    advanced_config = config_manager.get('advanced_indicators', default={})

    if not advanced_config.get('enabled', False):
        return {}

    ultimo_dato = datos.iloc[-1]
    dato_anterior = datos.iloc[-2]

    senales = {}

    try:
        # 1. Stochastic RSI
        if 'STOCHRSI_K' in ultimo_dato.index and 'STOCHRSI_D' in ultimo_dato.index:
            stoch_rsi_oversold = thresholds.get('stoch_rsi_oversold', 20)
            stoch_rsi_overbought = thresholds.get('stoch_rsi_overbought', 80)

            if (ultimo_dato['STOCHRSI_K'] < stoch_rsi_oversold and
                ultimo_dato['STOCHRSI_K'] > ultimo_dato['STOCHRSI_D'] and
                dato_anterior['STOCHRSI_K'] <= dato_anterior['STOCHRSI_D']):
                senales["Stochastic_RSI"] = "COMPRA"
            elif (ultimo_dato['STOCHRSI_K'] > stoch_rsi_overbought and
                  ultimo_dato['STOCHRSI_K'] < ultimo_dato['STOCHRSI_D'] and
                  dato_anterior['STOCHRSI_K'] >= dato_anterior['STOCHRSI_D']):
                senales["Stochastic_RSI"] = "VENTA"
            else:
                senales["Stochastic_RSI"] = "KEEP/NO SIGNAL"

        # 2. True Strength Index (TSI)
        if 'TSI' in ultimo_dato.index:
            tsi_bullish = thresholds.get('tsi_bullish', 5)
            tsi_bearish = thresholds.get('tsi_bearish', -5)

            if ultimo_dato['TSI'] > tsi_bullish:
                senales["TSI"] = "COMPRA"
            elif ultimo_dato['TSI'] < tsi_bearish:
                senales["TSI"] = "VENTA"
            else:
                senales["TSI"] = "KEEP/NO SIGNAL"

        # 3. Ultimate Oscillator
        if 'UO' in ultimo_dato.index:
            uo_oversold = thresholds.get('uo_oversold', 30)
            uo_overbought = thresholds.get('uo_overbought', 70)

            if ultimo_dato['UO'] < uo_oversold:
                senales["Ultimate_Oscillator"] = "COMPRA"
            elif ultimo_dato['UO'] > uo_overbought:
                senales["Ultimate_Oscillator"] = "VENTA"
            else:
                senales["Ultimate_Oscillator"] = "KEEP/NO SIGNAL"

        # 4. Chaikin Oscillator
        if 'CHAIKIN_OSC' in ultimo_dato.index:
            chaikin_bullish = thresholds.get('chaikin_bullish', 0)

            if ultimo_dato['CHAIKIN_OSC'] > chaikin_bullish and dato_anterior['CHAIKIN_OSC'] <= chaikin_bullish:
                senales["Chaikin_Oscillator"] = "COMPRA"
            elif ultimo_dato['CHAIKIN_OSC'] < chaikin_bullish and dato_anterior['CHAIKIN_OSC'] >= chaikin_bullish:
                senales["Chaikin_Oscillator"] = "VENTA"
            else:
                senales["Chaikin_Oscillator"] = "KEEP/NO SIGNAL"

        # 5. Aroon Oscillator
        if 'AROONOSC' in ultimo_dato.index:
            aroon_bullish = thresholds.get('aroon_osc_bullish', 50)
            aroon_bearish = thresholds.get('aroon_osc_bearish', -50)

            if ultimo_dato['AROONOSC'] > aroon_bullish:
                senales["Aroon_Oscillator"] = "COMPRA"
            elif ultimo_dato['AROONOSC'] < aroon_bearish:
                senales["Aroon_Oscillator"] = "VENTA"
            else:
                senales["Aroon_Oscillator"] = "KEEP/NO SIGNAL"

        # 6. TRIX
        if 'TRIX' in ultimo_dato.index:
            trix_bullish = thresholds.get('trix_bullish', 0)

            if ultimo_dato['TRIX'] > trix_bullish and dato_anterior['TRIX'] <= trix_bullish:
                senales["TRIX"] = "COMPRA"
            elif ultimo_dato['TRIX'] < trix_bullish and dato_anterior['TRIX'] >= trix_bullish:
                senales["TRIX"] = "VENTA"
            else:
                senales["TRIX"] = "KEEP/NO SIGNAL"

        # 7. Volume RSI
        if 'VOLRSI' in ultimo_dato.index:
            vol_rsi_oversold = thresholds.get('volume_rsi_oversold', 30)
            vol_rsi_overbought = thresholds.get('volume_rsi_overbought', 70)

            if ultimo_dato['VOLRSI'] < vol_rsi_oversold:
                senales["Volume_RSI"] = "COMPRA"
            elif ultimo_dato['VOLRSI'] > vol_rsi_overbought:
                senales["Volume_RSI"] = "VENTA"
            else:
                senales["Volume_RSI"] = "KEEP/NO SIGNAL"

        # 8. Detrended Price Oscillator
        if 'DPO' in ultimo_dato.index:
            dpo_bullish = thresholds.get('dpo_bullish', 0)

            if ultimo_dato['DPO'] > dpo_bullish and dato_anterior['DPO'] <= dpo_bullish:
                senales["DPO"] = "COMPRA"
            elif ultimo_dato['DPO'] < dpo_bullish and dato_anterior['DPO'] >= dpo_bullish:
                senales["DPO"] = "VENTA"
            else:
                senales["DPO"] = "KEEP/NO SIGNAL"

    except Exception as e:
        print(f"Error generando señales avanzadas: {e}")

    return senales

def get_advanced_indicator_values(datos: pd.DataFrame) -> Dict[str, Any]:
    """
    Obtiene los valores actuales de los indicadores avanzados para la tabla.

    Args:
        datos: DataFrame con datos y indicadores calculados

    Returns:
        Diccionario con valores de indicadores
    """
    if datos.empty:
        return {}

    advanced_config = config_manager.get('advanced_indicators', default={})
    if not advanced_config.get('enabled', False):
        return {}

    ultimo_dato = datos.iloc[-1]
    valores = {}

    try:
        # Nombres estándar definidos en advanced_indicators.py
        indicators = [
            'STOCHRSI_K', 'TSI', 'UO', 'CHAIKIN_OSC',
            'AROONOSC', 'TRIX', 'VOLRSI', 'DPO'
        ]

        # Extraer valores si existen
        for col in indicators:
            if col in ultimo_dato.index:
                valores[col] = ultimo_dato[col]

    except Exception as e:
        print(f"Error obteniendo valores de indicadores avanzados: {e}")

    return valores