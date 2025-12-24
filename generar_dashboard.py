"""Script para generar solo el dashboard consolidado con datos existentes."""

import os
import sys
import datetime
import pandas as pd
import data_storage
import indicator_calculator
import signal_generator
import dashboard_generator
from logger_config import get_logger
from config_manager import config_manager

logger = get_logger(__name__)

def main():
    """Genera el dashboard con datos ya procesados en la BD."""
    logger.info("Generando dashboard desde base de datos...")

    # Obtener rango de fechas (igual que en main.py)
    data_config = config_manager.get_data_config()
    analysis_days = data_config.get('analysis_period_days', 730)
    fecha_fin = datetime.date.today()
    fecha_inicio = fecha_fin - datetime.timedelta(days=analysis_days)

    logger.info(f"Usando rango de fechas: {fecha_inicio} a {fecha_fin} ({analysis_days} días)")

    # Leer tickers
    tickers_path = 'tickers.txt'
    with open(tickers_path, 'r', encoding='utf-8') as f:
        tickers = [line.strip() for line in f if line.strip()]

    logger.info(f"Procesando {len(tickers)} tickers desde la base de datos")

    ticker_data_collection = []

    for ticker in tickers:
        try:
            # Leer datos de la BD
            datos = data_storage.leer_datos(ticker)

            if datos is None or len(datos) == 0:
                logger.warning(f"No hay datos para {ticker}")
                continue

            # Filtrar por rango de fechas (mismo que main.py)
            # Convertir fecha_inicio y fecha_fin a datetime para comparar
            fecha_inicio_dt = pd.to_datetime(fecha_inicio)
            fecha_fin_dt = pd.to_datetime(fecha_fin)

            datos = datos[(datos['fecha'] >= fecha_inicio_dt) & (datos['fecha'] <= fecha_fin_dt)].copy()

            if len(datos) == 0:
                logger.warning(f"No hay datos en el rango de fechas para {ticker}")
                continue

            # Agregar columna ticker
            datos['ticker'] = ticker

            # Calcular indicadores
            datos_con_indicadores = indicator_calculator.calcular_indicadores(datos)
            datos_con_indicadores.dropna(inplace=True)

            if len(datos_con_indicadores) < 2:
                logger.warning(f"Datos insuficientes para {ticker}")
                continue

            # Generar señales
            resultado_analisis = signal_generator.generar_senales(datos_con_indicadores)

            # Obtener nombre de empresa (desde datos históricos)
            company_name = ticker  # Por defecto usar el ticker

            ticker_data_collection.append({
                'resultado_analisis': resultado_analisis,
                'company_name': company_name,
                'datos_con_indicadores': datos_con_indicadores
            })

            logger.info(f"✓ {ticker} procesado")

        except Exception as e:
            logger.error(f"Error procesando {ticker}: {e}")
            continue

    # Generar dashboard
    if ticker_data_collection:
        dashboard_path = dashboard_generator.generar_dashboard_consolidado(
            ticker_data_collection,
            "salidas"
        )
        logger.info(f"\n{'='*60}")
        logger.info(f"Dashboard generado exitosamente: {dashboard_path}")
        logger.info(f"{'='*60}")
    else:
        logger.error("No se pudieron procesar datos para generar el dashboard")

if __name__ == "__main__":
    main()
