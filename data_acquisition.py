"""
Módulo de Adquisición de Datos
===============================

Gestiona la descarga de datos históricos desde Yahoo Finance.
Incluye validaciones, conversión de formatos y manejo de errores.
"""

import yfinance as yf
import pandas as pd
from utils import rename_yfinance_columns, validate_ticker, validate_date_format, validate_required_columns
from constants import STANDARD_COLUMNS
from logger_config import get_logger

logger = get_logger(__name__)


def get_company_name(ticker: str) -> str:
    """
    Obtiene el nombre completo de la empresa para un ticker dado.

    Args:
        ticker: Símbolo del ticker

    Returns:
        Nombre completo de la empresa o ticker si falla

    Raises:
        ValueError: Si el ticker es inválido
    """
    if not ticker or not isinstance(ticker, str):
        logger.error(f"Ticker inválido: {ticker}")
        raise ValueError("El ticker debe ser una cadena no vacía")

    try:
        logger.debug(f"Obteniendo nombre de empresa para {ticker}")
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info:
            logger.warning(f"No se pudo obtener información para {ticker}")
            return ticker

        company_name = info.get('longName', ticker)
        logger.debug(f"Nombre obtenido: {company_name}")
        return company_name

    except Exception as e:
        logger.error(f"Error al obtener el nombre de la empresa para {ticker}: {e}")
        return ticker


def descargar_datos(ticker: str, fecha_inicio: str, fecha_fin: str) -> tuple:
    """
    Descarga datos históricos de precios de acciones desde Yahoo Finance.

    Args:
        ticker: El ticker de la acción (ej. "AAPL")
        fecha_inicio: La fecha de inicio en formato "YYYY-MM-DD"
        fecha_fin: La fecha de fin en formato "YYYY-MM-DD"

    Returns:
        Tuple (pd.DataFrame, str) con los datos de precios y el nombre de la empresa,
        o (None, None) si hay un error
    """
    # Validaciones de entrada
    try:
        validate_ticker(ticker)
    except ValueError as e:
        logger.error(f"Validación de ticker falló: {e}")
        return None, None

    if not fecha_inicio or not fecha_fin:
        logger.error("Las fechas de inicio y fin son requeridas")
        return None, None

    try:
        validate_date_format(fecha_inicio)
        validate_date_format(fecha_fin)
    except ValueError as e:
        logger.error(f"Validación de fecha falló: {e}")
        return None, None

    try:
        logger.info(f"Descargando datos para {ticker} desde {fecha_inicio} hasta {fecha_fin}")

        # Descargar datos desde Yahoo Finance
        datos = yf.download(
            ticker,
            start=fecha_inicio,
            end=fecha_fin,
            auto_adjust=False,
            progress=False
        )

        if datos.empty:
            logger.warning(f"No se encontraron datos para {ticker} en el rango especificado")
            return None, None

        # Manejar MultiIndex si existe
        if isinstance(datos.columns, pd.MultiIndex):
            logger.debug(f"Detectado MultiIndex, eliminando nivel adicional")
            datos.columns = datos.columns.droplevel(1)

        # Resetear índice para que fecha sea columna
        datos.reset_index(inplace=True)

        # Renombrar columnas al formato español estándar
        datos = rename_yfinance_columns(datos)
        logger.debug(f"Columnas renombradas a formato español")

        # Verificar que todas las columnas necesarias estén presentes
        required_columns = STANDARD_COLUMNS['SPANISH']
        try:
            validate_required_columns(datos, required_columns)
        except ValueError as e:
            logger.error(f"Faltan columnas requeridas: {e}")
            return None, None

        # Seleccionar solo las columnas necesarias
        datos = datos[required_columns]

        # Convertir fecha a datetime
        datos['fecha'] = pd.to_datetime(datos['fecha'])

        # Validar que los datos numéricos son válidos
        numeric_columns = ['apertura', 'maximo', 'minimo', 'cierre', 'volumen']
        for col in numeric_columns:
            if datos[col].isna().all():
                logger.error(f"Todos los valores de {col} son NaN para {ticker}")
                raise ValueError(f"Todos los valores de {col} son NaN")

        # Obtener nombre de la empresa
        company_name = get_company_name(ticker)

        logger.info(f"Descarga exitosa: {len(datos)} registros para {ticker} ({company_name})")
        logger.debug(f"Rango de fechas: {datos['fecha'].min()} a {datos['fecha'].max()}")

        return datos, company_name

    except Exception as e:
        logger.error(f"Error al descargar datos para {ticker}: {e}", exc_info=True)
        return None, None
