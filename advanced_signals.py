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
        stoch_rsi_col_k = f"STOCHRSI_K_{advanced_config.get('stoch_rsi_rsi_period', 14)}_{advanced_config.get('stoch_rsi_stoch_period', 14)}"
        stoch_rsi_col_d = f"STOCHRSI_D_{advanced_config.get('stoch_rsi_rsi_period', 14)}_{advanced_config.get('stoch_rsi_stoch_period', 14)}"

        if stoch_rsi_col_k in ultimo_dato.index and stoch_rsi_col_d in ultimo_dato.index:
            stoch_rsi_oversold = thresholds.get('stoch_rsi_oversold', 20)
            stoch_rsi_overbought = thresholds.get('stoch_rsi_overbought', 80)

            if (ultimo_dato[stoch_rsi_col_k] < stoch_rsi_oversold and
                ultimo_dato[stoch_rsi_col_k] > ultimo_dato[stoch_rsi_col_d] and
                dato_anterior[stoch_rsi_col_k] <= dato_anterior[stoch_rsi_col_d]):
                senales["Stochastic_RSI"] = "COMPRA"
            elif (ultimo_dato[stoch_rsi_col_k] > stoch_rsi_overbought and
                  ultimo_dato[stoch_rsi_col_k] < ultimo_dato[stoch_rsi_col_d] and
                  dato_anterior[stoch_rsi_col_k] >= dato_anterior[stoch_rsi_col_d]):
                senales["Stochastic_RSI"] = "VENTA"
            else:
                senales["Stochastic_RSI"] = "KEEP/NO SIGNAL"

        # 2. True Strength Index (TSI)
        tsi_col = f"TSI_{advanced_config.get('tsi_long_period', 25)}_{advanced_config.get('tsi_short_period', 13)}"
        if tsi_col in ultimo_dato.index:
            tsi_bullish = thresholds.get('tsi_bullish', 5)
            tsi_bearish = thresholds.get('tsi_bearish', -5)

            if ultimo_dato[tsi_col] > tsi_bullish:
                senales["TSI"] = "COMPRA"
            elif ultimo_dato[tsi_col] < tsi_bearish:
                senales["TSI"] = "VENTA"
            else:
                senales["TSI"] = "KEEP/NO SIGNAL"

        # 3. Ultimate Oscillator
        uo_col = f"UO_{advanced_config.get('uo_period1', 7)}_{advanced_config.get('uo_period2', 14)}_{advanced_config.get('uo_period3', 28)}"
        if uo_col in ultimo_dato.index:
            uo_oversold = thresholds.get('uo_oversold', 30)
            uo_overbought = thresholds.get('uo_overbought', 70)

            if ultimo_dato[uo_col] < uo_oversold:
                senales["Ultimate_Oscillator"] = "COMPRA"
            elif ultimo_dato[uo_col] > uo_overbought:
                senales["Ultimate_Oscillator"] = "VENTA"
            else:
                senales["Ultimate_Oscillator"] = "KEEP/NO SIGNAL"

        # 4. Chaikin Oscillator
        chaikin_col = f"CHAIKIN_OSC_{advanced_config.get('chaikin_fast', 3)}_{advanced_config.get('chaikin_slow', 10)}"
        if chaikin_col in ultimo_dato.index:
            chaikin_bullish = thresholds.get('chaikin_bullish', 0)

            if ultimo_dato[chaikin_col] > chaikin_bullish and dato_anterior[chaikin_col] <= chaikin_bullish:
                senales["Chaikin_Oscillator"] = "COMPRA"
            elif ultimo_dato[chaikin_col] < chaikin_bullish and dato_anterior[chaikin_col] >= chaikin_bullish:
                senales["Chaikin_Oscillator"] = "VENTA"
            else:
                senales["Chaikin_Oscillator"] = "KEEP/NO SIGNAL"

        # 5. Aroon Oscillator
        aroon_osc_col = f"AROONOSC_{advanced_config.get('aroon_period', 14)}"
        if aroon_osc_col in ultimo_dato.index:
            aroon_bullish = thresholds.get('aroon_osc_bullish', 50)
            aroon_bearish = thresholds.get('aroon_osc_bearish', -50)

            if ultimo_dato[aroon_osc_col] > aroon_bullish:
                senales["Aroon_Oscillator"] = "COMPRA"
            elif ultimo_dato[aroon_osc_col] < aroon_bearish:
                senales["Aroon_Oscillator"] = "VENTA"
            else:
                senales["Aroon_Oscillator"] = "KEEP/NO SIGNAL"

        # 6. TRIX
        trix_col = f"TRIX_{advanced_config.get('trix_period', 14)}"
        if trix_col in ultimo_dato.index:
            trix_bullish = thresholds.get('trix_bullish', 0)

            if ultimo_dato[trix_col] > trix_bullish and dato_anterior[trix_col] <= trix_bullish:
                senales["TRIX"] = "COMPRA"
            elif ultimo_dato[trix_col] < trix_bullish and dato_anterior[trix_col] >= trix_bullish:
                senales["TRIX"] = "VENTA"
            else:
                senales["TRIX"] = "KEEP/NO SIGNAL"

        # 7. Volume RSI
        volume_rsi_col = f"VOLRSI_{advanced_config.get('volume_rsi_period', 14)}"
        if volume_rsi_col in ultimo_dato.index:
            vol_rsi_oversold = thresholds.get('volume_rsi_oversold', 30)
            vol_rsi_overbought = thresholds.get('volume_rsi_overbought', 70)

            if ultimo_dato[volume_rsi_col] < vol_rsi_oversold:
                senales["Volume_RSI"] = "COMPRA"
            elif ultimo_dato[volume_rsi_col] > vol_rsi_overbought:
                senales["Volume_RSI"] = "VENTA"
            else:
                senales["Volume_RSI"] = "KEEP/NO SIGNAL"

        # 8. Detrended Price Oscillator
        dpo_col = f"DPO_{advanced_config.get('dpo_period', 20)}"
        if dpo_col in ultimo_dato.index:
            dpo_bullish = thresholds.get('dpo_bullish', 0)

            if ultimo_dato[dpo_col] > dpo_bullish and dato_anterior[dpo_col] <= dpo_bullish:
                senales["DPO"] = "COMPRA"
            elif ultimo_dato[dpo_col] < dpo_bullish and dato_anterior[dpo_col] >= dpo_bullish:
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
        # Definir nombres de columnas basados en configuración
        indicators = {
            'STOCHRSI_K': f"STOCHRSI_K_{advanced_config.get('stoch_rsi_rsi_period', 14)}_{advanced_config.get('stoch_rsi_stoch_period', 14)}",
            'TSI': f"TSI_{advanced_config.get('tsi_long_period', 25)}_{advanced_config.get('tsi_short_period', 13)}",
            'UO': f"UO_{advanced_config.get('uo_period1', 7)}_{advanced_config.get('uo_period2', 14)}_{advanced_config.get('uo_period3', 28)}",
            'CHAIKIN_OSC': f"CHAIKIN_OSC_{advanced_config.get('chaikin_fast', 3)}_{advanced_config.get('chaikin_slow', 10)}",
            'AROONOSC': f"AROONOSC_{advanced_config.get('aroon_period', 14)}",
            'TRIX': f"TRIX_{advanced_config.get('trix_period', 14)}",
            'VOLRSI': f"VOLRSI_{advanced_config.get('volume_rsi_period', 14)}",
            'DPO': f"DPO_{advanced_config.get('dpo_period', 20)}"
        }

        # Extraer valores si existen
        for key, col in indicators.items():
            if col in ultimo_dato.index:
                valores[key] = ultimo_dato[col]

    except Exception as e:
        print(f"Error obteniendo valores de indicadores avanzados: {e}")

    return valores