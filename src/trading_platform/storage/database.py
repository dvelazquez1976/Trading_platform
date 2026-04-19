"""Almacenamiento persistente en SQLite con bulk insert."""

import sqlite3
import pandas as pd
from contextlib import contextmanager
from pathlib import Path

from trading_platform.core.constants import DB_DIR
from trading_platform.core.logging import get_logger

logger = get_logger(__name__)

DB_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_FILE = DB_DIR / "plataforma_trading.db"


@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def crear_base_de_datos():
    with get_db_connection() as conn:
        conn.execute('''
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
    logger.info(f"Base de datos inicializada: {DATABASE_FILE}")


def guardar_datos(datos: pd.DataFrame, ticker: str):
    if datos is None or datos.empty:
        raise ValueError("Datos vacíos")
    required = ['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen']
    missing = [c for c in required if c not in datos.columns]
    if missing:
        raise ValueError(f"Faltan columnas: {missing}")

    df = datos.copy()
    df['ticker'] = ticker
    df['fecha'] = df['fecha'].astype(str)

    records = [
        (row['ticker'], row['fecha'], row['apertura'], row['maximo'],
         row['minimo'], row['cierre'], row['volumen'])
        for _, row in df.iterrows()
    ]

    with get_db_connection() as conn:
        conn.executemany('''
            INSERT OR REPLACE INTO precios_acciones
            (ticker, fecha, apertura, maximo, minimo, cierre, volumen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', records)

    logger.info(f"Guardados {len(records)} registros para {ticker}")


def leer_datos(ticker: str) -> pd.DataFrame:
    with get_db_connection() as conn:
        return pd.read_sql(
            "SELECT fecha, apertura, maximo, minimo, cierre, volumen "
            "FROM precios_acciones WHERE ticker = ? ORDER BY fecha",
            conn, params=[ticker], parse_dates=['fecha']
        )


def contar_registros(ticker: str = None) -> int:
    with get_db_connection() as conn:
        cur = conn.cursor()
        if ticker:
            cur.execute('SELECT COUNT(*) FROM precios_acciones WHERE ticker = ?', (ticker,))
        else:
            cur.execute('SELECT COUNT(*) FROM precios_acciones')
        return cur.fetchone()[0]
