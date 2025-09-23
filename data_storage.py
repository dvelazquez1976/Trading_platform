import sqlite3
import pandas as pd

def crear_base_de_datos():
    """Crea la base de datos y la tabla si no existen."""
    try:
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
        print("Base de datos creada exitosamente.")
    except sqlite3.Error as e:
        print(f"Error al crear la base de datos: {e}")
        raise
    finally:
        if conn:
            conn.close()

def guardar_datos(datos, ticker):
    """Guarda los datos de precios en la base de datos, actualizando duplicados."""
    if datos is None or datos.empty:
        raise ValueError("Los datos no pueden estar vacíos")

    if not ticker or not isinstance(ticker, str):
        raise ValueError("El ticker debe ser una cadena no vacía")

    conn = None
    try:
        conn = sqlite3.connect('plataforma_trading.db')
        datos_copia = datos.copy()
        datos_copia['ticker'] = ticker

        # Validar columnas requeridas
        required_columns = ['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen']
        missing_columns = [col for col in required_columns if col not in datos_copia.columns]
        if missing_columns:
            raise ValueError(f"Faltan columnas requeridas: {missing_columns}")

        # Usar INSERT OR REPLACE para actualizar datos existentes
        cursor = conn.cursor()
        for _, row in datos_copia.iterrows():
            # Convertir fecha a string si es necesario
            fecha_str = row['fecha'].strftime('%Y-%m-%d') if hasattr(row['fecha'], 'strftime') else str(row['fecha'])
            cursor.execute('''
                INSERT OR REPLACE INTO precios_acciones
                (ticker, fecha, apertura, maximo, minimo, cierre, volumen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (row['ticker'], fecha_str, row['apertura'], row['maximo'],
                  row['minimo'], row['cierre'], row['volumen']))

        conn.commit()
        print(f"Datos guardados/actualizados exitosamente para {ticker}.")

    except sqlite3.Error as e:
        print(f"Error de base de datos al guardar {ticker}: {e}")
        raise
    except Exception as e:
        print(f"Error inesperado al guardar {ticker}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def leer_datos(ticker):
    """Lee los datos de precios de un ticker desde la base de datos."""
    if not ticker or not isinstance(ticker, str):
        raise ValueError("El ticker debe ser una cadena no vacía")

    conn = None
    try:
        conn = sqlite3.connect('plataforma_trading.db')
        query = "SELECT fecha, apertura, maximo, minimo, cierre, volumen FROM precios_acciones WHERE ticker = ? ORDER BY fecha"
        datos = pd.read_sql(query, conn, params=[ticker], parse_dates=['fecha'])

        if datos.empty:
            print(f"No se encontraron datos para el ticker {ticker}.")

        return datos

    except sqlite3.Error as e:
        print(f"Error de base de datos al leer {ticker}: {e}")
        raise
    except Exception as e:
        print(f"Error inesperado al leer {ticker}: {e}")
        raise
    finally:
        if conn:
            conn.close()
