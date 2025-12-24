"""
Plataforma de Trading - Módulo Principal
==========================================

Este módulo orquesta el flujo completo de análisis de trading:
1. Lectura de tickers desde archivo
2. Descarga de datos históricos
3. Almacenamiento en base de datos
4. Cálculo de indicadores técnicos
5. Generación de señales de trading
6. Visualización de resultados
7. Exportación a CSV y tablas

Autor: Trading Platform Team
Fecha: 2025
"""

import datetime
import os
import sys
from io import StringIO
from typing import List, Tuple, Dict, Any

import pandas as pd
from tabulate import tabulate

# Importaciones de módulos locales
import data_acquisition
import data_storage
import indicator_calculator
import signal_generator
import visualizer
import dashboard_generator
from csv_formatter import modify_csv_format
from parallel_processor import ParallelProcessor, process_single_ticker
from config_manager import config_manager
from utils import (
    prepare_summary_table_row, prepare_signals_table_row,
    prepare_values_table_row, get_summary_table_headers,
    get_signals_table_headers, get_values_table_headers
)
from constants import CSV_DATA_TYPES
from logger_config import get_logger

# Configuración del logger
logger = get_logger(__name__)

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class TradingPlatform:
    """
    Clase principal que gestiona el flujo de ejecución de la plataforma de trading.
    """

    def __init__(self):
        """Inicializa la plataforma de trading."""
        self.tickers: List[str] = []
        self.fecha_inicio: datetime.date = None
        self.fecha_fin: datetime.date = None
        self.ticker_data_collection: List[Dict[str, Any]] = []
        self.all_historical_data: List[pd.DataFrame] = []
        self.salidas_dir = os.path.join(BASE_DIR, 'salidas')

        logger.info("="*80)
        logger.info("PLATAFORMA DE TRADING - INICIO DE EJECUCIÓN")
        logger.info("="*80)

    def load_tickers(self, tickers_file: str = 'tickers.txt') -> bool:
        """
        Carga los tickers desde el archivo especificado.

        Args:
            tickers_file: Nombre del archivo con los tickers

        Returns:
            True si se cargaron correctamente, False en caso contrario
        """
        tickers_path = os.path.join(BASE_DIR, tickers_file)

        try:
            logger.info(f"Cargando tickers desde: {tickers_path}")

            with open(tickers_path, 'r', encoding='utf-8') as f:
                self.tickers = [line.strip() for line in f if line.strip()]

            logger.info(f"Cargados {len(self.tickers)} tickers: {', '.join(self.tickers)}")
            return True

        except FileNotFoundError:
            logger.error(f"No se encontró el archivo de tickers: {tickers_path}")
            logger.error("Asegúrese de que el archivo 'tickers.txt' existe")
            return False
        except IOError as e:
            logger.error(f"Error al leer el archivo de tickers: {e}")
            return False

    def setup_date_range(self, analysis_days: int = 730):
        """
        Configura el rango de fechas para el análisis.

        Args:
            analysis_days: Número de días a analizar (por defecto 730 = 2 años)
        """
        # Usamos mañana como fecha de fin porque yfinance excluye el día de fin
        self.fecha_fin = datetime.date.today() + datetime.timedelta(days=1)
        self.fecha_inicio = self.fecha_fin - datetime.timedelta(days=analysis_days)

        logger.info(f"Rango de análisis configurado:")
        logger.info(f"  Fecha inicio: {self.fecha_inicio.strftime('%Y-%m-%d')}")
        logger.info(f"  Fecha fin (exclusiva): {self.fecha_fin.strftime('%Y-%m-%d')}")
        logger.info(f"  Días de análisis: {analysis_days}")

    def process_ticker_sequential(self, ticker: str) -> bool:
        """
        Procesa un ticker individual de forma secuencial.

        Args:
            ticker: Símbolo del ticker a procesar

        Returns:
            True si se procesó correctamente, False en caso contrario
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"PROCESANDO: {ticker}")
        logger.info(f"{'='*60}")

        try:
            # 1. Descarga de datos
            logger.debug(f"[{ticker}] Descargando datos históricos...")
            datos_historicos, company_name = data_acquisition.descargar_datos(
                ticker,
                self.fecha_inicio.strftime("%Y-%m-%d"),
                self.fecha_fin.strftime("%Y-%m-%d")
            )

            if datos_historicos is None:
                logger.warning(f"[{ticker}] No se pudieron obtener datos. Saltando...")
                return False

            # Añadir ticker column
            datos_historicos['ticker'] = ticker
            self.all_historical_data.append(datos_historicos)

            # 2. Almacenamiento en base de datos
            logger.debug(f"[{ticker}] Guardando datos en base de datos...")
            data_storage.guardar_datos(datos_historicos, ticker)

            # 3. Uso de datos frescos (evitar lectura innecesaria de DB)
            datos_frescos = datos_historicos.copy()

            # 4. Cálculo de indicadores técnicos
            logger.debug(f"[{ticker}] Calculando indicadores técnicos...")
            datos_con_indicadores = indicator_calculator.calcular_indicadores(datos_frescos)

            # Limpieza de NaN
            datos_con_indicadores.dropna(inplace=True)

            if len(datos_con_indicadores) < 2:
                logger.warning(f"[{ticker}] Datos insuficientes para generar señales")
                return False

            # 5. Generación de señales
            logger.debug(f"[{ticker}] Generando señales de trading...")
            resultado_analisis = signal_generator.generar_senales(datos_con_indicadores)

            # 6. Generación de gráficos
            logger.debug(f"[{ticker}] Generando gráfico interactivo...")
            visualizer.generar_grafico(
                datos_con_indicadores,
                resultado_analisis,
                ticker,
                self.salidas_dir
            )

            # Guardar resultados para tablas
            self.ticker_data_collection.append({
                'resultado_analisis': resultado_analisis,
                'company_name': company_name,
                'datos_con_indicadores': datos_con_indicadores
            })

            logger.info(f"[{ticker}] Procesamiento completado exitosamente")
            return True

        except Exception as e:
            logger.error(f"[{ticker}] Error durante el procesamiento: {e}", exc_info=True)
            return False

    def process_all_tickers_sequential(self):
        """Procesa todos los tickers de forma secuencial."""
        logger.info("\n" + "="*80)
        logger.info("MODO DE PROCESAMIENTO: SECUENCIAL")
        logger.info("="*80 + "\n")

        success_count = 0
        for ticker in self.tickers:
            if self.process_ticker_sequential(ticker):
                success_count += 1

        logger.info(f"\nProcesamiento secuencial completado: {success_count}/{len(self.tickers)} exitosos")

    def process_all_tickers_parallel(self, max_workers: int = 4):
        """
        Procesa todos los tickers en paralelo.

        Args:
            max_workers: Número máximo de workers paralelos
        """
        logger.info("\n" + "="*80)
        logger.info(f"MODO DE PROCESAMIENTO: PARALELO ({max_workers} workers)")
        logger.info("="*80 + "\n")

        processor = ParallelProcessor(max_workers=max_workers)

        parallel_results = processor.process_tickers_parallel(
            self.tickers,
            process_single_ticker,
            self.fecha_inicio.strftime("%Y-%m-%d"),
            self.fecha_fin.strftime("%Y-%m-%d"),
            self.salidas_dir
        )

        # Procesar resultados
        for ticker, result in parallel_results:
            if result is None:
                logger.warning(f"No se pudieron obtener datos para {ticker}")
                continue

            # Extraer datos
            datos_historicos = result['datos_historicos']
            datos_con_indicadores = result['datos_con_indicadores']
            resultado_analisis = result['resultado_analisis']
            company_name = result['company_name']

            # Añadir ticker column y guardar
            datos_historicos['ticker'] = ticker
            self.all_historical_data.append(datos_historicos)

            # Guardar para construcción de tablas
            self.ticker_data_collection.append({
                'resultado_analisis': resultado_analisis,
                'company_name': company_name,
                'datos_con_indicadores': datos_con_indicadores
            })

        logger.info(f"Procesamiento paralelo completado")

    def export_csv_data(self):
        """Exporta datos históricos a archivos CSV."""
        if not self.all_historical_data:
            logger.warning("No hay datos históricos para exportar a CSV")
            return

        logger.info("\n" + "="*80)
        logger.info("EXPORTACIÓN DE DATOS A CSV")
        logger.info("="*80)

        # Concatenar todos los datos históricos
        full_historical_df = pd.concat(self.all_historical_data, ignore_index=True)

        # Crear directorio de salidas
        os.makedirs(self.salidas_dir, exist_ok=True)

        # Exportar cada tipo de dato
        for original_col, csv_name in CSV_DATA_TYPES.items():
            logger.debug(f"Generando CSV para: {original_col}")

            try:
                # Crear tabla pivote
                pivot_df = full_historical_df.pivot_table(
                    index='ticker',
                    columns='fecha',
                    values=original_col
                )

                # Guardar CSV
                csv_file_path = os.path.join(self.salidas_dir, f"{csv_name}_data.csv")
                pivot_df.to_csv(csv_file_path)

                # Modificar formato para Excel
                success, message = modify_csv_format(csv_file_path, csv_file_path)

                if success:
                    logger.info(f"✓ {csv_name}_data.csv generado y formateado")
                else:
                    logger.warning(f"CSV generado pero error en formato: {message}")

            except Exception as e:
                logger.error(f"Error generando CSV {csv_name}: {e}")

    def generate_summary_tables(self) -> str:
        """
        Genera las tablas de resumen de resultados.

        Returns:
            String con todas las tablas formateadas
        """
        if not self.ticker_data_collection:
            logger.warning("No hay datos para generar tablas")
            return ""

        logger.info("\n" + "="*80)
        logger.info("GENERACIÓN DE TABLAS DE RESULTADOS")
        logger.info("="*80)

        # Capturar output de tablas
        tablas_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = tablas_output

        try:
            # Obtener configuración de indicadores avanzados
            advanced_config = config_manager.get('advanced_indicators', default={})
            advanced_enabled = advanced_config.get('enabled', False)

            # TABLA 1: Resumen General
            summary_data = [
                prepare_summary_table_row(
                    data['resultado_analisis'],
                    data['company_name']
                )
                for data in self.ticker_data_collection
            ]

            print("\n" + "="*80)
            print("TABLA 1: RESUMEN GENERAL")
            print("="*80)
            print(tabulate(summary_data, headers=get_summary_table_headers(), tablefmt="grid"))

            # TABLA 2: Señales de Indicadores Básicos
            signals_basic_data = [
                prepare_signals_table_row(data['resultado_analisis'], basic=True)
                for data in self.ticker_data_collection
            ]

            print("\n" + "="*80)
            print("TABLA 2: SEÑALES DE INDICADORES BÁSICOS")
            print("="*80)
            print(tabulate(signals_basic_data, headers=get_signals_table_headers(basic=True), tablefmt="grid"))

            # TABLA 3: Valores de Indicadores Básicos
            values_basic_data = [
                prepare_values_table_row(
                    data['resultado_analisis'],
                    data['datos_con_indicadores'],
                    basic=True
                )
                for data in self.ticker_data_collection
            ]

            print("\n" + "="*80)
            print("TABLA 3: VALORES DE INDICADORES BÁSICOS")
            print("="*80)
            print(tabulate(values_basic_data, headers=get_values_table_headers(basic=True), tablefmt="grid"))

            # Tablas de indicadores avanzados (si están habilitados)
            if advanced_enabled:
                logger.debug("Generando tablas de indicadores avanzados...")

                # TABLA 4: Señales Avanzadas
                signals_advanced_data = [
                    prepare_signals_table_row(data['resultado_analisis'], basic=False)
                    for data in self.ticker_data_collection
                ]

                print("\n" + "="*80)
                print("TABLA 4: SEÑALES DE INDICADORES AVANZADOS")
                print("="*80)
                print(tabulate(signals_advanced_data, headers=get_signals_table_headers(basic=False), tablefmt="grid"))

                # TABLA 5: Valores Avanzados
                values_advanced_data = [
                    prepare_values_table_row(
                        data['resultado_analisis'],
                        data['datos_con_indicadores'],
                        basic=False
                    )
                    for data in self.ticker_data_collection
                ]

                print("\n" + "="*80)
                print("TABLA 5: VALORES DE INDICADORES AVANZADOS")
                print("="*80)
                print(tabulate(values_advanced_data, headers=get_values_table_headers(basic=False), tablefmt="grid"))

        finally:
            sys.stdout = original_stdout

        logger.info("Tablas generadas exitosamente")
        return tablas_output.getvalue()

    def save_results(self, tablas_content: str):
        """
        Guarda las tablas de resultados en salida.txt.

        Args:
            tablas_content: Contenido de las tablas a guardar
        """
        salida_path = os.path.join(BASE_DIR, 'salida.txt')

        try:
            with open(salida_path, 'w', encoding='utf-8') as f:
                f.write(tablas_content)
            logger.info(f"Tablas guardadas en: {salida_path}")
        except IOError as e:
            logger.error(f"Error guardando resultados: {e}")

    def _initialize_system(self) -> bool:
        """Inicializa los componentes básicos del sistema."""
        try:
            logger.info("Inicializando base de datos...")
            data_storage.crear_base_de_datos()

            if not self.load_tickers():
                return False

            data_config = config_manager.get_data_config()
            analysis_days = data_config.get('analysis_period_days', 730)
            self.setup_date_range(analysis_days)
            return True
        except Exception as e:
            logger.error(f"Error en inicialización: {e}")
            return False

    def _process_data(self):
        """Gestiona el procesamiento de tickers (secuencial o paralelo)."""
        processing_config = config_manager.get('processing', default={})
        use_parallel = processing_config.get('parallel_processing', False)
        max_workers = processing_config.get('max_workers', 4)

        if use_parallel and len(self.tickers) > 1:
            self.process_all_tickers_parallel(max_workers)
        else:
            self.process_all_tickers_sequential()

    def _generate_outputs(self):
        """Genera todos los archivos de salida y reportes."""
        # 1. Exportar datos a CSV
        self.export_csv_data()

        # 2. Generar tablas de resumen
        tablas_content = self.generate_summary_tables()

        # 3. Guardar resultados en texto
        self.save_results(tablas_content)

        # 4. Generar dashboard consolidado
        dashboard_path = dashboard_generator.generar_dashboard_consolidado(
            self.ticker_data_collection,
            self.salidas_dir
        )
        return dashboard_path

    def run(self):
        """Ejecuta el flujo completo de la plataforma."""
        try:
            if not self._initialize_system():
                logger.error("Fallo en la inicialización del sistema. Abortando.")
                return

            self._process_data()
            
            if not self.ticker_data_collection:
                logger.warning("No se procesaron datos. No se generarán salidas.")
                return

            dashboard_path = self._generate_outputs()

            # Resumen final
            self._log_final_summary(dashboard_path)

        except Exception as e:
            logger.error(f"Error crítico durante la ejecución: {e}", exc_info=True)
            raise

    def _log_final_summary(self, dashboard_path: str):
        """Muestra el resumen final de la ejecución."""
        logger.info("\n" + "="*80)
        logger.info("ANÁLISIS COMPLETADO EXITOSAMENTE")
        logger.info("="*80)
        logger.info(f"✓ Tickers procesados: {len(self.ticker_data_collection)}/{len(self.tickers)}")
        logger.info(f"✓ Mensajes de control: control.txt")
        logger.info(f"✓ Tablas de resultados: salida.txt")
        logger.info(f"✓ Archivos CSV: {self.salidas_dir}/")
        logger.info(f"✓ Gráficos HTML: {self.salidas_dir}/")
        logger.info(f"✓ Dashboard consolidado: {dashboard_path}")
        logger.info("="*80)


def main():
    """Punto de entrada principal del programa."""
    platform = TradingPlatform()
    platform.run()


if __name__ == "__main__":
    main()
