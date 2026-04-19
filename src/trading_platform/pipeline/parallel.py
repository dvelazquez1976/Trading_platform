"""Procesador paralelo de tickers."""

import concurrent.futures
import threading
import time
from typing import List, Tuple, Callable, Any

from trading_platform.core.logging import get_logger

logger = get_logger(__name__)


class ParallelProcessor:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.errors: List[Tuple[str, str]] = []
        self.lock = threading.Lock()

    def process_tickers_parallel(self, tickers: List[str], fn: Callable, *args, **kwargs) -> List[Tuple[str, Any]]:
        results = []
        self.errors = []
        t0 = time.time()
        logger.info(f"Procesando {len(tickers)} tickers con {self.max_workers} workers")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures = {ex.submit(self._run_one, t, fn, *args, **kwargs): t for t in tickers}
            for fut in concurrent.futures.as_completed(futures):
                ticker, result = fut.result()
                if result is not None:
                    results.append((ticker, result))

        logger.info(f"Paralelo completado en {time.time()-t0:.1f}s — {len(results)} OK, {len(self.errors)} errores")
        return results

    def _run_one(self, ticker: str, fn: Callable, *args, **kwargs) -> Tuple[str, Any]:
        try:
            t0 = time.time()
            result = fn(ticker, *args, **kwargs)
            logger.info(f"{ticker} procesado en {time.time()-t0:.2f}s")
            return ticker, result
        except Exception as e:
            with self.lock:
                self.errors.append((ticker, str(e)))
            logger.error(f"Error procesando {ticker}: {e}")
            return ticker, None


def process_single_ticker(ticker: str, fecha_inicio: str, fecha_fin: str, output_dir: str = None) -> dict:
    """Procesa un ticker completo — apto para uso en paralelo."""
    from trading_platform.providers import descargar_datos
    from trading_platform.storage import guardar_datos
    from trading_platform.indicators.basic import calcular_indicadores
    from trading_platform.signals.generator import generar_senales
    from trading_platform.visualization.charts import generar_grafico

    try:
        datos, company_name = descargar_datos(ticker, fecha_inicio, fecha_fin)
        if datos is None:
            return None

        datos['ticker'] = ticker
        guardar_datos(datos, ticker)

        df = calcular_indicadores(datos.copy())
        df.dropna(inplace=True)
        if len(df) < 2:
            return None

        resultado = generar_senales(df)
        generar_grafico(df, resultado, ticker, output_dir)

        return {
            'datos_historicos': datos,
            'datos_con_indicadores': df,
            'resultado_analisis': resultado,
            'company_name': company_name
        }
    except Exception as e:
        logger.error(f"Error en {ticker}: {e}", exc_info=True)
        return None
