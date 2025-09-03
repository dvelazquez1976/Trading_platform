import yfinance as yf
import pandas as pd

def get_company_name(ticker):
    """
    Obtiene el nombre completo de la empresa para un ticker dado.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info.get('longName', ticker) # Return longName or ticker if not found
    except Exception as e:
        print(f"Error al obtener el nombre de la empresa para {ticker}: {e}")
        return ticker # Fallback to ticker if error

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
    try:
        datos = yf.download(ticker, start=fecha_inicio, end=fecha_fin, auto_adjust=False)
        if datos.empty:
            print(f"No se encontraron datos para {ticker} en el rango de fechas especificado.")
            return None, None
        
        if isinstance(datos.columns, pd.MultiIndex):
            datos.columns = datos.columns.droplevel(1)

        datos.reset_index(inplace=True)
        datos.rename(columns={"Date": "fecha", "Open": "apertura", "High": "maximo", "Low": "minimo", "Close": "cierre", "Volume": "volumen"}, inplace=True)
        datos = datos[['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen']]
        datos['fecha'] = pd.to_datetime(datos['fecha'])
        
        company_name = get_company_name(ticker) # Get company name
        
        return datos, company_name
    except Exception as e:
        print(f"Error al descargar datos para {ticker}: {e}")
    return None, None
