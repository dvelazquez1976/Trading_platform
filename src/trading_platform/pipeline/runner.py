"""Orquestador principal del pipeline de análisis."""

import datetime
import os
from io import StringIO
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from tabulate import tabulate

from trading_platform.core.config import config_manager
from trading_platform.core.constants import CSV_DATA_TYPES, REPORTS_DIR, CSV_DIR
from trading_platform.core.logging import get_logger
from trading_platform.core.utils import (
    modify_csv_format, prepare_summary_table_row, prepare_signals_table_row,
    prepare_values_table_row, get_summary_table_headers,
    get_signals_table_headers, get_values_table_headers
)
from trading_platform.providers import descargar_datos
from trading_platform.storage.database import crear_base_de_datos, guardar_datos
from trading_platform.indicators.basic import calcular_indicadores
from trading_platform.signals.generator import generar_senales
from trading_platform.visualization.charts import generar_grafico
from trading_platform.visualization.dashboard import generar_dashboard_consolidado
from trading_platform.pipeline.parallel import ParallelProcessor, process_single_ticker

logger = get_logger(__name__)


class TradingPlatform:
    def __init__(self, output_dir: str = None):
        self.tickers: List[str] = []
        self.fecha_inicio: datetime.date = None
        self.fecha_fin:    datetime.date = None
        self.ticker_data:  List[Dict[str, Any]] = []
        self.all_historical: List[pd.DataFrame] = []
        self.output_dir = output_dir or str(REPORTS_DIR)

    # ── Public API ─────────────────────────────────────────────────────────

    def run(self):
        if not self._init():
            return
        self._process()
        if not self.ticker_data:
            logger.warning("Sin datos procesados.")
            return
        self._generate_outputs()

    def run_tickers(self, tickers: List[str], analysis_days: int = 730) -> List[Dict]:
        """API pública para llamadas desde Streamlit."""
        self.tickers = tickers
        self._setup_dates(analysis_days)
        crear_base_de_datos()
        self._process()
        return self.ticker_data

    # ── Init ───────────────────────────────────────────────────────────────

    def _init(self) -> bool:
        crear_base_de_datos()
        cfg = config_manager.get_data_config()
        self._setup_dates(cfg.get('analysis_period_days', 730))
        tickers_file = Path(config_manager.get('data', 'tickers_file', 'data/watchlists/default.csv'))
        if not tickers_file.exists():
            # fallback a tickers.txt raíz
            tickers_file = Path('tickers.txt')
        try:
            with open(tickers_file, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith('ticker')]
                # soporta CSV (ticker,name,sector) o txt simple
                self.tickers = [l.split(',')[0] for l in lines]
            logger.info(f"Cargados {len(self.tickers)} tickers de {tickers_file}")
            return bool(self.tickers)
        except Exception as e:
            logger.error(f"Error cargando tickers: {e}")
            return False

    def _setup_dates(self, days: int):
        self.fecha_fin    = datetime.date.today() + datetime.timedelta(days=1)
        self.fecha_inicio = self.fecha_fin - datetime.timedelta(days=days)

    # ── Processing ─────────────────────────────────────────────────────────

    def _process(self):
        cfg = config_manager.get('processing', default={})
        if cfg.get('parallel_processing', False) and len(self.tickers) > 1:
            self._process_parallel(cfg.get('max_workers', 4))
        else:
            self._process_sequential()

    def _process_sequential(self):
        for ticker in self.tickers:
            result = self._process_one(ticker)
            if result:
                self.ticker_data.append(result)

    def _process_parallel(self, workers: int):
        processor = ParallelProcessor(max_workers=workers)
        results = processor.process_tickers_parallel(
            self.tickers, process_single_ticker,
            self.fecha_inicio.strftime('%Y-%m-%d'),
            self.fecha_fin.strftime('%Y-%m-%d'),
            self.output_dir
        )
        for ticker, res in results:
            if res:
                self.all_historical.append(res['datos_historicos'])
                self.ticker_data.append({
                    'resultado_analisis':   res['resultado_analisis'],
                    'company_name':         res['company_name'],
                    'datos_con_indicadores': res['datos_con_indicadores']
                })

    def _process_one(self, ticker: str) -> Dict | None:
        try:
            datos, company_name = descargar_datos(
                ticker,
                self.fecha_inicio.strftime('%Y-%m-%d'),
                self.fecha_fin.strftime('%Y-%m-%d')
            )
            if datos is None:
                return None

            datos['ticker'] = ticker
            self.all_historical.append(datos)
            guardar_datos(datos, ticker)

            df = calcular_indicadores(datos.copy())
            df.dropna(inplace=True)
            if len(df) < 2:
                return None

            resultado = generar_senales(df)
            generar_grafico(df, resultado, ticker, self.output_dir)
            return {'resultado_analisis': resultado, 'company_name': company_name, 'datos_con_indicadores': df}

        except Exception as e:
            logger.error(f"Error procesando {ticker}: {e}", exc_info=True)
            return None

    # ── Outputs ────────────────────────────────────────────────────────────

    def _generate_outputs(self):
        self._export_csv()
        generar_dashboard_consolidado(self.ticker_data, self.output_dir)

    def _export_csv(self):
        if not self.all_historical:
            return
        CSV_DIR.mkdir(parents=True, exist_ok=True)
        full = pd.concat(self.all_historical, ignore_index=True)
        for col, name in CSV_DATA_TYPES.items():
            try:
                pivot = full.pivot_table(index='ticker', columns='fecha', values=col)
                path = str(CSV_DIR / f"{name}_data.csv")
                pivot.to_csv(path)
                modify_csv_format(path, path)
            except Exception as e:
                logger.warning(f"CSV {name}: {e}")
