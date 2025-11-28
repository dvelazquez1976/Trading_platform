import concurrent.futures
import threading
from typing import List, Tuple, Callable, Any
import time
from logger_config import get_logger

logger = get_logger(__name__)

class ParallelProcessor:
    """Procesador paralelo para análisis de múltiples tickers."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.results = []
        self.errors = []
        self.lock = threading.Lock()
        logger.info(f"ParallelProcessor inicializado con {max_workers} workers")

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
            logger.debug(f"Iniciando procesamiento de {ticker}")
            start_time = time.time()
            result = process_function(ticker, *args, **kwargs)
            processing_time = time.time() - start_time

            with self.lock:
                logger.info(f"{ticker} procesado exitosamente en {processing_time:.2f}s")

            return ticker, result

        except Exception as e:
            with self.lock:
                logger.error(f"Error procesando {ticker}: {str(e)}", exc_info=True)
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

        logger.info(f"Iniciando procesamiento paralelo de {len(tickers)} tickers con {self.max_workers} workers")
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar todos los trabajos
            future_to_ticker = {
                executor.submit(self.process_ticker, ticker, process_function, *args, **kwargs): ticker
                for ticker in tickers
            }
            logger.debug(f"{len(future_to_ticker)} tareas enviadas al pool de workers")

            # Recopilar resultados conforme se completan
            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    ticker, result = future.result()
                    if result is not None:
                        self.results.append((ticker, result))
                except Exception as e:
                    with self.lock:
                        logger.error(f"Error inesperado procesando {ticker}: {str(e)}", exc_info=True)
                        self.errors.append((ticker, str(e)))

        total_time = time.time() - start_time
        success_count = len(self.results)
        error_count = len(self.errors)

        logger.info(
            f"Procesamiento paralelo completado en {total_time:.2f}s - "
            f"Exitosos: {success_count}, Errores: {error_count}"
        )

        if self.errors:
            logger.warning(f"Se encontraron {error_count} errores durante el procesamiento:")
            for ticker, error in self.errors:
                logger.warning(f"  - {ticker}: {error}")

        return self.results

    def get_results(self) -> List[Tuple[str, Any]]:
        """Obtiene los resultados del procesamiento."""
        return self.results

    def get_errors(self) -> List[Tuple[str, str]]:
        """Obtiene los errores del procesamiento."""
        return self.errors

def process_single_ticker(ticker: str, fecha_inicio: str, fecha_fin: str, output_dir: str = "salidas") -> dict:
    """
    Función auxiliar para procesar un ticker individual.
    Esta función encapsula todo el proceso de análisis de un ticker.

    Args:
        ticker: El ticker a procesar
        fecha_inicio: Fecha de inicio del análisis
        fecha_fin: Fecha de fin del análisis
        output_dir: Directorio de salida para archivos HTML

    Returns:
        Diccionario con los resultados del análisis
    """
    import data_acquisition
    import data_storage
    import indicator_calculator
    import signal_generator
    import visualizer

    try:
        logger.info(f"Iniciando análisis completo para {ticker}")

        # 1. Adquisición de Datos
        logger.debug(f"[{ticker}] Paso 1/6: Adquisición de datos")
        datos_historicos, company_name = data_acquisition.descargar_datos(
            ticker, fecha_inicio, fecha_fin
        )

        if datos_historicos is None:
            logger.warning(f"No se obtuvieron datos para {ticker}")
            return None

        # 2. Almacenamiento de Datos
        logger.debug(f"[{ticker}] Paso 2/6: Almacenamiento en base de datos")
        data_storage.guardar_datos(datos_historicos, ticker)

        # 3. Cargar Datos desde la Base de Datos
        logger.debug(f"[{ticker}] Paso 3/6: Carga de datos desde BD")
        datos_desde_db = data_storage.leer_datos(ticker)
        datos_desde_db['ticker'] = ticker

        # 4. Cálculo de Indicadores Técnicos
        logger.debug(f"[{ticker}] Paso 4/6: Cálculo de indicadores técnicos")
        datos_con_indicadores = indicator_calculator.calcular_indicadores(datos_desde_db)

        # Asegurarse de que no haya valores NaN que afecten el análisis de señales
        datos_con_indicadores.dropna(inplace=True)

        if len(datos_con_indicadores) < 2:
            logger.warning(f"Datos insuficientes para generar señales en {ticker} (< 2 registros)")
            return None

        # 5. Generación de Señales
        logger.debug(f"[{ticker}] Paso 5/6: Generación de señales de trading")
        resultado_analisis = signal_generator.generar_senales(datos_con_indicadores)

        # 6. Generación de Gráficos
        logger.debug(f"[{ticker}] Paso 6/6: Generación de gráfico interactivo")
        visualizer.generar_grafico(datos_con_indicadores, resultado_analisis, ticker, output_dir)

        logger.info(f"Análisis completo para {ticker} finalizado exitosamente")

        return {
            'datos_historicos': datos_historicos,
            'datos_con_indicadores': datos_con_indicadores,
            'resultado_analisis': resultado_analisis,
            'company_name': company_name
        }

    except Exception as e:
        logger.error(f"Error procesando {ticker}: {e}", exc_info=True)
        return None