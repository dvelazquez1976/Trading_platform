import yfinance as yf
import pandas as pd
from utils import rename_yfinance_columns, validate_ticker, validate_date_format, validate_required_columns
from constants import STANDARD_COLUMNS

def get_company_name(ticker):
    """
    Obtiene el nombre completo de la empresa para un ticker dado.
    """
    if not ticker or not isinstance(ticker, str):
        raise ValueError("El ticker debe ser una cadena no vacía")

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info:
            print(f"No se pudo obtener información para {ticker}")
            return ticker
        return info.get('longName', ticker)
    except Exception as e:
        print(f"Error al obtener el nombre de la empresa para {ticker}: {e}")
        return ticker

def descargar_datos(ticker, fecha_inicio, fecha_fin):
    """
    Descarga datos históricos de precios de acciones desde Yahoo Finance.

    Args:
        ticker (str): El ticker de la acción (ej. "AAPL").
        fecha_inicio (str): La fecha de inicio en formato "YYYY-MM-DD".
        fecha_fin (str): La fecha de fin en formato "YYYY-MM-DD".

    Returns:
        tuple: Un tuple (pd.DataFrame, str) con los datos de precios y el nombre de la empresa, o (None, None) si hay un error.
    """
    # Validaciones de entrada
    validate_ticker(ticker)

    if not fecha_inicio or not fecha_fin:
        raise ValueError("Las fechas de inicio y fin son requeridas")

    validate_date_format(fecha_inicio)
    validate_date_format(fecha_fin)

    try:
        print(f"Descargando datos para {ticker} desde {fecha_inicio} hasta {fecha_fin}...")
        datos = yf.download(ticker, start=fecha_inicio, end=fecha_fin, auto_adjust=False, progress=False)

        if datos.empty:
            print(f"No se encontraron datos para {ticker} en el rango de fechas especificado.")
            return None, None

        # Manejar MultiIndex si existe
        if isinstance(datos.columns, pd.MultiIndex):
            datos.columns = datos.columns.droplevel(1)

        datos.reset_index(inplace=True)
        datos = rename_yfinance_columns(datos)

        # Verificar que todas las columnas necesarias estén presentes
        required_columns = STANDARD_COLUMNS['SPANISH']
        validate_required_columns(datos, required_columns)

        datos = datos[required_columns]
        datos['fecha'] = pd.to_datetime(datos['fecha'])

        # Validar que los datos numéricos son válidos
        numeric_columns = ['apertura', 'maximo', 'minimo', 'cierre', 'volumen']
        for col in numeric_columns:
            if datos[col].isna().all():
                raise ValueError(f"Todos los valores de {col} son NaN")

        company_name = get_company_name(ticker)
        print(f"Descarga exitosa: {len(datos)} registros para {ticker}")

        return datos, company_name

    except Exception as e:
        print(f"Error al descargar datos para {ticker}: {e}")
        return None, None
