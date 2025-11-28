"""
Módulo de Almacenamiento de Datos
==================================

Gestiona el almacenamiento persistente de datos en SQLite.
Incluye operaciones CRUD y gestión de conexiones.
"""

import sqlite3
import pandas as pd
from contextlib import contextmanager
from constants import DEFAULT_PATHS
from logger_config import get_logger

logger = get_logger(__name__)

# Configuración de base de datos
DATABASE_NAME = DEFAULT_PATHS.get('database_file', 'plataforma_trading.db')


@contextmanager
def get_db_connection():
    """
    Context manager para manejar conexiones a la base de datos.

    Yields:
        sqlite3.Connection: Conexión a la base de datos

    Raises:
        sqlite3.Error: Si hay error de base de datos
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        logger.debug(f"Conexión a base de datos establecida: {DATABASE_NAME}")
        yield conn
        conn.commit()
        logger.debug("Transacción confirmada")
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            logger.error(f"Error en base de datos, rollback ejecutado: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.debug("Conexión a base de datos cerrada")


def crear_base_de_datos():
    """
    Crea la base de datos y la tabla si no existen.

    Raises:
        sqlite3.Error: Si hay error al crear la base de datos
    """
    try:
        logger.info(f"Inicializando base de datos: {DATABASE_NAME}")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS precios_acciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    fecha DATE NOT NULL,
                    apertura REAL NOT NULL,
                    maximo REAL NOT NULL,
                    minimo REAL NOT NULL,
                    cierre REAL NOT NULL,
                    volumen INTEGER NOT NULL,
                    UNIQUE(ticker, fecha)
                )
            ''')

        logger.info(f"Base de datos '{DATABASE_NAME}' inicializada correctamente")

    except sqlite3.Error as e:
        logger.error(f"Error al crear la base de datos: {e}", exc_info=True)
        raise


def _validar_datos_entrada(datos: pd.DataFrame, ticker: str):
    """
    Valida los datos de entrada antes de guardar.

    Args:
        datos: DataFrame con datos a validar
        ticker: Ticker de la acción

    Raises:
        ValueError: Si los datos no son válidos
    """
    if datos is None or datos.empty:
        logger.error("Intento de guardar datos vacíos")
        raise ValueError("Los datos no pueden estar vacíos")

    if not ticker or not isinstance(ticker, str):
        logger.error(f"Ticker inválido: {ticker}")
        raise ValueError("El ticker debe ser una cadena no vacía")

    required_columns = ['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen']
    missing_columns = [col for col in required_columns if col not in datos.columns]

    if missing_columns:
        logger.error(f"Faltan columnas requeridas: {missing_columns}")
        raise ValueError(f"Faltan columnas requeridas: {missing_columns}")

    logger.debug(f"Validación de datos exitosa para {ticker}")


def _formatear_fecha(fecha) -> str:
    """
    Formatea una fecha para almacenamiento.

    Args:
        fecha: Fecha en formato datetime o string

    Returns:
        Fecha formateada como string YYYY-MM-DD
    """
    if hasattr(fecha, 'strftime'):
        return fecha.strftime('%Y-%m-%d')
    return str(fecha)


def guardar_datos(datos: pd.DataFrame, ticker: str):
    """
    Guarda los datos de precios en la base de datos, actualizando duplicados.

    Args:
        datos: DataFrame con datos de precios
        ticker: Ticker de la acción

    Raises:
        ValueError: Si los datos no son válidos
        sqlite3.Error: Si hay error en la base de datos
    """
    _validar_datos_entrada(datos, ticker)

    try:
        logger.info(f"Guardando {len(datos)} registros para {ticker}")

        with get_db_connection() as conn:
            datos_copia = datos.copy()
            datos_copia['ticker'] = ticker

            cursor = conn.cursor()
            registros_actualizados = 0
            registros_nuevos = 0

            for _, row in datos_copia.iterrows():
                fecha_str = _formatear_fecha(row['fecha'])

                # Verificar si el registro existe
                cursor.execute(
                    'SELECT id FROM precios_acciones WHERE ticker = ? AND fecha = ?',
                    (row['ticker'], fecha_str)
                )
                existe = cursor.fetchone()

                cursor.execute('''
                    INSERT OR REPLACE INTO precios_acciones
                    (ticker, fecha, apertura, maximo, minimo, cierre, volumen)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (row['ticker'], fecha_str, row['apertura'], row['maximo'],
                      row['minimo'], row['cierre'], row['volumen']))

                if existe:
                    registros_actualizados += 1
                else:
                    registros_nuevos += 1

        logger.info(
            f"Datos guardados para {ticker}: "
            f"{registros_nuevos} nuevos, {registros_actualizados} actualizados"
        )

    except sqlite3.Error as e:
        logger.error(f"Error de base de datos al guardar {ticker}: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error inesperado al guardar {ticker}: {e}", exc_info=True)
        raise


def leer_datos(ticker: str) -> pd.DataFrame:
    """
    Lee los datos de precios de un ticker desde la base de datos.

    Args:
        ticker: Ticker de la acción

    Returns:
        DataFrame con datos de precios históricos

    Raises:
        ValueError: Si el ticker no es válido
        sqlite3.Error: Si hay error en la base de datos
    """
    if not ticker or not isinstance(ticker, str):
        logger.error(f"Ticker inválido para lectura: {ticker}")
        raise ValueError("El ticker debe ser una cadena no vacía")

    try:
        logger.debug(f"Leyendo datos de {ticker} desde base de datos")

        with get_db_connection() as conn:
            query = """
                SELECT fecha, apertura, maximo, minimo, cierre, volumen
                FROM precios_acciones
                WHERE ticker = ?
                ORDER BY fecha
            """
            datos = pd.read_sql(query, conn, params=[ticker], parse_dates=['fecha'])

            if datos.empty:
                logger.warning(f"No se encontraron datos para el ticker {ticker}")
            else:
                logger.info(
                    f"Datos leídos para {ticker}: {len(datos)} registros, "
                    f"rango {datos['fecha'].min()} a {datos['fecha'].max()}"
                )

            return datos

    except sqlite3.Error as e:
        logger.error(f"Error de base de datos al leer {ticker}: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error inesperado al leer {ticker}: {e}", exc_info=True)
        raise


def contar_registros(ticker: str = None) -> int:
    """
    Cuenta el número de registros en la base de datos.

    Args:
        ticker: Ticker específico (None para todos)

    Returns:
        Número de registros
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if ticker:
                cursor.execute(
                    'SELECT COUNT(*) FROM precios_acciones WHERE ticker = ?',
                    (ticker,)
                )
            else:
                cursor.execute('SELECT COUNT(*) FROM precios_acciones')

            count = cursor.fetchone()[0]
            logger.debug(f"Registros en DB{' para ' + ticker if ticker else ''}: {count}")
            return count

    except sqlite3.Error as e:
        logger.error(f"Error al contar registros: {e}")
        return 0


def eliminar_ticker(ticker: str) -> int:
    """
    Elimina todos los datos de un ticker específico.

    Args:
        ticker: Ticker a eliminar

    Returns:
        Número de registros eliminados
    """
    if not ticker or not isinstance(ticker, str):
        logger.error(f"Ticker inválido para eliminación: {ticker}")
        raise ValueError("El ticker debe ser una cadena no vacía")

    try:
        logger.warning(f"Eliminando todos los datos de {ticker}")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM precios_acciones WHERE ticker = ?', (ticker,))
            deleted = cursor.rowcount

        logger.info(f"Eliminados {deleted} registros de {ticker}")
        return deleted

    except sqlite3.Error as e:
        logger.error(f"Error al eliminar {ticker}: {e}", exc_info=True)
        raise
