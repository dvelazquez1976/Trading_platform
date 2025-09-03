import pandas as pd

def generar_senales(datos):
    """
    Analiza los indicadores más recientes y genera un diccionario de señales.

    Args:
        datos (pd.DataFrame): DataFrame con los precios y los indicadores.

    Returns:
        dict: Un diccionario con las señales de cada indicador.
    """
    senales = {
        "Cruce_Medias": "KEEP/NO SIGNAL",
        "RSI": "KEEP/NO SIGNAL",
        "Estocastico": "KEEP/NO SIGNAL",
        "MACD": "KEEP/NO SIGNAL",
        "Bandas_Bollinger": "KEEP/NO SIGNAL",
        "Williams_R": "KEEP/NO SIGNAL",
        "Awesome_Oscillator": "KEEP/NO SIGNAL",
        "ROC": "KEEP/NO SIGNAL"
    }

    ultimo_dato = datos.iloc[-1]
    dato_anterior = datos.iloc[-2]

    # 1. Cruce de Medias Móviles (SMA_30 vs SMA_60)
    if ultimo_dato['SMA_30'] > ultimo_dato['SMA_60'] and dato_anterior['SMA_30'] <= dato_anterior['SMA_60']:
        senales["Cruce_Medias"] = "COMPRA"
    elif ultimo_dato['SMA_30'] < ultimo_dato['SMA_60'] and dato_anterior['SMA_30'] >= dato_anterior['SMA_60']:
        senales["Cruce_Medias"] = "VENTA"

    # 2. RSI
    if ultimo_dato['RSI_14'] < 30:
        senales["RSI"] = "COMPRA"
    elif ultimo_dato['RSI_14'] > 70:
        senales["RSI"] = "VENTA"

    # 3. Estocástico
    if ultimo_dato['STOCHk_14_3_3'] < 20 and ultimo_dato['STOCHd_14_3_3'] < 20 and \
       ultimo_dato['STOCHk_14_3_3'] > ultimo_dato['STOCHd_14_3_3'] and dato_anterior['STOCHk_14_3_3'] <= dato_anterior['STOCHd_14_3_3']:
        senales["Estocastico"] = "COMPRA"
    elif ultimo_dato['STOCHk_14_3_3'] > 80 and ultimo_dato['STOCHd_14_3_3'] > 80 and \
         ultimo_dato['STOCHk_14_3_3'] < ultimo_dato['STOCHd_14_3_3'] and dato_anterior['STOCHk_14_3_3'] >= dato_anterior['STOCHd_14_3_3']:
        senales["Estocastico"] = "VENTA"

    # 4. MACD
    if ultimo_dato['MACD_12_26_9'] > ultimo_dato['MACDs_12_26_9'] and dato_anterior['MACD_12_26_9'] <= dato_anterior['MACDs_12_26_9']:
        senales["MACD"] = "COMPRA"
    elif ultimo_dato['MACD_12_26_9'] < ultimo_dato['MACDs_12_26_9'] and dato_anterior['MACD_12_26_9'] >= dato_anterior['MACDs_12_26_9']:
        senales["MACD"] = "VENTA"

    # 5. Bandas de Bollinger
    if ultimo_dato['cierre'] < ultimo_dato['BBL_20_2']:
        senales["Bandas_Bollinger"] = "COMPRA"
    elif ultimo_dato['cierre'] > ultimo_dato['BBU_20_2']:
        senales["Bandas_Bollinger"] = "VENTA"

    # 6. Williams %R
    if ultimo_dato['WILLR_14'] < -80:
        senales["Williams_R"] = "COMPRA"
    elif ultimo_dato['WILLR_14'] > -20:
        senales["Williams_R"] = "VENTA"

    # 7. Awesome Oscillator
    if ultimo_dato['AO_5_34'] > 0 and dato_anterior['AO_5_34'] <= 0:
        senales["Awesome_Oscillator"] = "COMPRA"
    elif ultimo_dato['AO_5_34'] < 0 and dato_anterior['AO_5_34'] >= 0:
        senales["Awesome_Oscillator"] = "VENTA"

    # 8. Rate of Change (ROC)
    if ultimo_dato['ROC_12'] > 5:
        senales["ROC"] = "COMPRA"
    elif ultimo_dato['ROC_12'] < -5:
        senales["ROC"] = "VENTA"

    # Resumen de recomendación
    compras = list(senales.values()).count("COMPRA")
    ventas = list(senales.values()).count("VENTA")

    if compras > ventas:
        resumen = "COMPRA"
    elif ventas > compras:
        resumen = "VENTA"
    else:
        resumen = "KEEP"

    resultado = {
        "ticker": ultimo_dato['ticker'],
        "fecha": ultimo_dato['fecha'].strftime('%Y-%m-%d'),
        "precio_cierre": ultimo_dato['cierre'],
        "señales": senales,
        "resumen": resumen
    }

    return resultado
