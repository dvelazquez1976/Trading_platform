import sqlite3
import pandas as pd

def crear_base_de_datos():
    """Crea la base de datos y la tabla si no existen."""
    conn = sqlite3.connect('plataforma_trading.db')
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
    conn.commit()
    conn.close()

def guardar_datos(datos, ticker):
    """Guarda los datos de precios en la base de datos, evitando duplicados."""
    conn = sqlite3.connect('plataforma_trading.db')
    datos['ticker'] = ticker
    try:
        datos.to_sql('precios_acciones', conn, if_exists='append', index=False)
    except sqlite3.IntegrityError:
        # Evitar duplicados
        pass
    conn.close()

def leer_datos(ticker):
    """Lee los datos de precios de un ticker desde la base de datos."""
    conn = sqlite3.connect('plataforma_trading.db')
    query = f"SELECT fecha, apertura, maximo, minimo, cierre, volumen FROM precios_acciones WHERE ticker = '{ticker}' ORDER BY fecha"
    datos = pd.read_sql(query, conn, parse_dates=['fecha'])
    conn.close()
    return datos
