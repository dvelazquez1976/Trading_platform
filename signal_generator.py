"""Generador de señales de trading basadas en indicadores técnicos."""

import pandas as pd
from typing import Dict, Tuple
from config_manager import config_manager
from advanced_signals import generate_advanced_signals
from logger_config import get_logger

logger = get_logger(__name__)

# Constantes para señales
SIGNAL_BUY = "COMPRA"
SIGNAL_SELL = "VENTA"
SIGNAL_HOLD = "KEEP/NO SIGNAL"


def _get_last_two_rows(datos: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    Obtiene las últimas dos filas del DataFrame para análisis.

    Args:
        datos: DataFrame con datos históricos

    Returns:
        Tupla con (último_dato, dato_anterior)
    """
    return datos.iloc[-1], datos.iloc[-2]


def _evaluar_cruce(valor_actual: float, valor_ref_actual: float,
                   valor_anterior: float, valor_ref_anterior: float) -> str:
    """
    Evalúa si hay un cruce entre dos valores.

    Args:
        valor_actual: Valor actual del indicador
        valor_ref_actual: Valor de referencia actual
        valor_anterior: Valor anterior del indicador
        valor_ref_anterior: Valor de referencia anterior

    Returns:
        Señal de trading (COMPRA, VENTA, o KEEP/NO SIGNAL)
    """
    if valor_actual > valor_ref_actual and valor_anterior <= valor_ref_anterior:
        return SIGNAL_BUY
    elif valor_actual < valor_ref_actual and valor_anterior >= valor_ref_anterior:
        return SIGNAL_SELL
    return SIGNAL_HOLD


def _evaluar_umbral(valor: float, umbral_inferior: float, umbral_superior: float) -> str:
    """
    Evalúa si un valor está fuera de umbrales.

    Args:
        valor: Valor a evaluar
        umbral_inferior: Umbral inferior (oversold)
        umbral_superior: Umbral superior (overbought)

    Returns:
        Señal de trading
    """
    if valor < umbral_inferior:
        return SIGNAL_BUY
    elif valor > umbral_superior:
        return SIGNAL_SELL
    return SIGNAL_HOLD


def _inicializar_senales() -> Dict[str, str]:
    """
    Inicializa el diccionario de señales con valores por defecto.

    Returns:
        Diccionario de señales inicializado
    """
    return {
        "Cruce_Medias": SIGNAL_HOLD,
        "RSI": SIGNAL_HOLD,
        "Estocastico": SIGNAL_HOLD,
        "MACD": SIGNAL_HOLD,
        "Bandas_Bollinger": SIGNAL_HOLD,
        "Williams_R": SIGNAL_HOLD,
        "Awesome_Oscillator": SIGNAL_HOLD,
        "ROC": SIGNAL_HOLD
    }


def generar_senales(datos: pd.DataFrame) -> Dict:
    """
    Analiza los indicadores más recientes y genera un diccionario de señales.

    Args:
        datos: DataFrame con los precios y los indicadores.

    Returns:
        Diccionario con las señales de cada indicador y resumen.
    """
    ticker = datos.iloc[-1]['ticker'] if 'ticker' in datos.columns else 'Unknown'
    logger.info(f"Generando señales de trading para {ticker}")

    thresholds = config_manager.get_signal_thresholds()
    logger.debug(f"Umbrales de señales cargados: {thresholds}")

    senales = _inicializar_senales()
    ultimo_dato, dato_anterior = _get_last_two_rows(datos)
    logger.debug(f"Analizando datos del {ultimo_dato['fecha'].strftime('%Y-%m-%d')}")

    # 1. Cruce de Medias Móviles (SMA_30 vs SMA_60)
    senales["Cruce_Medias"] = _evaluar_cruce(
        ultimo_dato['SMA_30'], ultimo_dato['SMA_60'],
        dato_anterior['SMA_30'], dato_anterior['SMA_60']
    )

    # 2. RSI
    senales["RSI"] = _evaluar_umbral(
        ultimo_dato['RSI'],
        thresholds.get('rsi_oversold', 30),
        thresholds.get('rsi_overbought', 70)
    )

    # 3. Estocástico
    stoch_oversold = thresholds.get('stoch_oversold', 20)
    stoch_overbought = thresholds.get('stoch_overbought', 80)

    # Cruce en zona de sobreventa
    if (ultimo_dato['STOCHk'] < stoch_oversold and
        ultimo_dato['STOCHd'] < stoch_oversold):
        senales["Estocastico"] = _evaluar_cruce(
            ultimo_dato['STOCHk'], ultimo_dato['STOCHd'],
            dato_anterior['STOCHk'], dato_anterior['STOCHd']
        )
    # Cruce en zona de sobrecompra
    elif (ultimo_dato['STOCHk'] > stoch_overbought and
          ultimo_dato['STOCHd'] > stoch_overbought):
        cruce = _evaluar_cruce(
            ultimo_dato['STOCHk'], ultimo_dato['STOCHd'],
            dato_anterior['STOCHk'], dato_anterior['STOCHd']
        )
        # Invertir señal en zona de sobrecompra
        if cruce == SIGNAL_BUY:
            senales["Estocastico"] = SIGNAL_SELL
        elif cruce == SIGNAL_SELL:
            senales["Estocastico"] = SIGNAL_BUY

    # 4. MACD
    senales["MACD"] = _evaluar_cruce(
        ultimo_dato['MACD'], ultimo_dato['MACDs'],
        dato_anterior['MACD'], dato_anterior['MACDs']
    )

    # 5. Bandas de Bollinger
    if ultimo_dato['cierre'] < ultimo_dato['BBL_BB']:
        senales["Bandas_Bollinger"] = SIGNAL_BUY
    elif ultimo_dato['cierre'] > ultimo_dato['BBU_BB']:
        senales["Bandas_Bollinger"] = SIGNAL_SELL

    # 6. Williams %R
    senales["Williams_R"] = _evaluar_umbral(
        ultimo_dato['WILLR'],
        thresholds.get('willr_oversold', -80),
        thresholds.get('willr_overbought', -20)
    )

    # 7. Awesome Oscillator
    senales["Awesome_Oscillator"] = _evaluar_cruce(
        ultimo_dato['AO'], 0,
        dato_anterior['AO'], 0
    )

    # 8. Rate of Change (ROC)
    roc_bullish = thresholds.get('roc_bullish', 5)
    roc_bearish = thresholds.get('roc_bearish', -5)
    if ultimo_dato['ROC'] > roc_bullish:
        senales["ROC"] = SIGNAL_BUY
    elif ultimo_dato['ROC'] < roc_bearish:
        senales["ROC"] = SIGNAL_SELL

    # Generar señales avanzadas si están habilitadas
    senales_avanzadas = generate_advanced_signals(datos)
    if senales_avanzadas:
        logger.debug(f"Señales avanzadas generadas: {len(senales_avanzadas)}")
        senales.update(senales_avanzadas)

    # Calcular resumen
    resumen = _calcular_resumen(senales)

    # Contar señales
    compras = list(senales.values()).count(SIGNAL_BUY)
    ventas = list(senales.values()).count(SIGNAL_SELL)
    holds = list(senales.values()).count(SIGNAL_HOLD)

    logger.info(
        f"Señales generadas para {ticker}: {compras} COMPRA, {ventas} VENTA, "
        f"{holds} HOLD → Resumen: {resumen}"
    )
    logger.debug(f"Detalle de señales: {senales}")

    return _construir_resultado(ultimo_dato, senales, resumen)


def _calcular_resumen(senales: Dict[str, str]) -> str:
    """
    Calcula la recomendación general basada en las señales.

    Args:
        senales: Diccionario de señales

    Returns:
        Resumen de la recomendación (COMPRA, VENTA, o KEEP)
    """
    valores = list(senales.values())
    compras = valores.count(SIGNAL_BUY)
    ventas = valores.count(SIGNAL_SELL)

    if compras > ventas:
        return "COMPRA"
    elif ventas > compras:
        return "VENTA"
    return "KEEP"


def _construir_resultado(ultimo_dato: pd.Series, senales: Dict[str, str],
                        resumen: str) -> Dict:
    """
    Construye el diccionario de resultado final.

    Args:
        ultimo_dato: Última fila de datos
        senales: Diccionario de señales
        resumen: Resumen de recomendación

    Returns:
        Diccionario con resultado completo
    """
    return {
        "ticker": ultimo_dato['ticker'],
        "fecha": ultimo_dato['fecha'].strftime('%Y-%m-%d'),
        "precio_cierre": ultimo_dato['cierre'],
        "señales": senales,
        "resumen": resumen
    }
