import concurrent.futures
import threading
from typing import List, Tuple, Callable, Any
import time

class ParallelProcessor:
    """Procesador paralelo para análisis de múltiples tickers."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.results = []
        self.errors = []
        self.lock = threading.Lock()

    def process_ticker(self, ticker: str, process_function: Callable, *args, **kwargs) -> Tuple[str, Any]:
        """
        Procesa un ticker individual.

        Args:
            ticker: El ticker a procesar
            process_function: Función que procesa el ticker
            *args, **kwargs: Argumentos adicionales para la función

        Returns:
            Tuple con el ticker y el resultado
        """
        try:
            start_time = time.time()
            result = process_function(ticker, *args, **kwargs)
            processing_time = time.time() - start_time

            with self.lock:
                print(f"✓ {ticker} procesado en {processing_time:.2f}s")

            return ticker, result

        except Exception as e:
            with self.lock:
                error_msg = f"✗ Error procesando {ticker}: {str(e)}"
                print(error_msg)
                self.errors.append((ticker, str(e)))

            return ticker, None

    def process_tickers_parallel(self, tickers: List[str], process_function: Callable,
                                *args, **kwargs) -> List[Tuple[str, Any]]:
        """
        Procesa múltiples tickers en paralelo.

        Args:
            tickers: Lista de tickers a procesar
            process_function: Función que procesa cada ticker
            *args, **kwargs: Argumentos adicionales para la función

        Returns:
            Lista de tuplas (ticker, resultado)
        """
        self.results = []
        self.errors = []

        print(f"Iniciando procesamiento paralelo de {len(tickers)} tickers con {self.max_workers} workers...")
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar todos los trabajos
            future_to_ticker = {
                executor.submit(self.process_ticker, ticker, process_function, *args, **kwargs): ticker
                for ticker in tickers
            }

            # Recopilar resultados conforme se completan
            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    ticker, result = future.result()
                    if result is not None:
                        self.results.append((ticker, result))
                except Exception as e:
                    with self.lock:
                        error_msg = f"Error inesperado procesando {ticker}: {str(e)}"
                        print(error_msg)
                        self.errors.append((ticker, str(e)))

        total_time = time.time() - start_time
        success_count = len(self.results)
        error_count = len(self.errors)

        print(f"Procesamiento completado en {total_time:.2f}s")
        print(f"Exitosos: {success_count}, Errores: {error_count}")

        if self.errors:
            print("Errores encontrados:")
            for ticker, error in self.errors:
                print(f"  - {ticker}: {error}")

        return self.results

    def get_results(self) -> List[Tuple[str, Any]]:
        """Obtiene los resultados del procesamiento."""
        return self.results

    def get_errors(self) -> List[Tuple[str, str]]:
        """Obtiene los errores del procesamiento."""
        return self.errors

def process_single_ticker(ticker: str, fecha_inicio: str, fecha_fin: str) -> dict:
    """
    Función auxiliar para procesar un ticker individual.
    Esta función encapsula todo el proceso de análisis de un ticker.

    Args:
        ticker: El ticker a procesar
        fecha_inicio: Fecha de inicio del análisis
        fecha_fin: Fecha de fin del análisis

    Returns:
        Diccionario con los resultados del análisis
    """
    import data_acquisition
    import data_storage
    import indicator_calculator
    import signal_generator
    import visualizer

    try:
        # 1. Adquisición de Datos
        print(f"Descargando datos para {ticker}...")
        datos_historicos, company_name = data_acquisition.descargar_datos(
            ticker, fecha_inicio, fecha_fin
        )

        if datos_historicos is None:
            return None

        # 2. Almacenamiento de Datos
        print(f"Guardando datos en la base de datos para {ticker}...")
        data_storage.guardar_datos(datos_historicos, ticker)

        # 3. Cargar Datos desde la Base de Datos
        print(f"Cargando datos desde la base de datos para {ticker}...")
        datos_desde_db = data_storage.leer_datos(ticker)
        datos_desde_db['ticker'] = ticker

        # 4. Cálculo de Indicadores Técnicos
        print(f"Calculando indicadores técnicos para {ticker}...")
        datos_con_indicadores = indicator_calculator.calcular_indicadores(datos_desde_db)

        # Asegurarse de que no haya valores NaN que afecten el análisis de señales
        datos_con_indicadores.dropna(inplace=True)

        if len(datos_con_indicadores) < 2:
            print(f"No hay suficientes datos para generar señales para {ticker}.")
            return None

        # 5. Generación de Señales
        print(f"Generando señales de trading para {ticker}...")
        resultado_analisis = signal_generator.generar_senales(datos_con_indicadores)

        # 6. Generación de Gráficos
        print(f"Generando gráfico interactivo para {ticker}...")
        visualizer.generar_grafico(datos_con_indicadores, resultado_analisis, ticker)

        return {
            'datos_historicos': datos_historicos,
            'datos_con_indicadores': datos_con_indicadores,
            'resultado_analisis': resultado_analisis,
            'company_name': company_name
        }

    except Exception as e:
        print(f"Error procesando {ticker}: {e}")
        return None