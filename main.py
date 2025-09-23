import data_acquisition
import data_storage
import indicator_calculator
import signal_generator
import visualizer
from csv_formatter import modify_csv_format
from parallel_processor import ParallelProcessor, process_single_ticker
from config_manager import config_manager
from utils import prepare_table_row, get_dynamic_table_headers
from constants import CSV_DATA_TYPES
import datetime
import json
import sys
import pandas as pd
from tabulate import tabulate
import os

# Definir el directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__name__))

def main():
    """Flujo de ejecución principal del sistema de análisis de trading."""
    # Crear la base de datos y la tabla si no existen
    data_storage.crear_base_de_datos()

    # Leer tickers desde tickers.txt
    tickers_path = os.path.join(BASE_DIR, 'tickers.txt')
    try:
        with open(tickers_path, 'r') as f:
            tickers = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de tickers en la ruta: {tickers_path}")
        print("Por favor, asegúrese de que el archivo 'tickers.txt' exista en el directorio correcto.")
        return
    except IOError as e:
        print(f"Error al leer el archivo de tickers: {e}")
        return

    # Redirigir la salida a Salida.txt
    salida_path = os.path.join(BASE_DIR, 'Salida.txt')
    original_stdout = sys.stdout
    try:
        with open(salida_path, 'w') as f_salida:
            sys.stdout = f_salida

            # Obtener configuración
            data_config = config_manager.get_data_config()
            processing_config = config_manager.get('processing', default={})

            # Definir el rango de fechas para el análisis
            fecha_fin = datetime.date.today()
            analysis_days = data_config.get('analysis_period_days', 730)
            fecha_inicio = fecha_fin - datetime.timedelta(days=analysis_days)

            all_results = []
            all_historical_data = [] # To collect all historical data for CSV export

            # Decidir si usar procesamiento paralelo
            use_parallel = processing_config.get('parallel_processing', False)
            max_workers = processing_config.get('max_workers', 4)

            if use_parallel and len(tickers) > 1:
                print(f"Usando procesamiento paralelo con {max_workers} workers...")
                processor = ParallelProcessor(max_workers=max_workers)

                # Procesar todos los tickers en paralelo
                parallel_results = processor.process_tickers_parallel(
                    tickers,
                    process_single_ticker,
                    fecha_inicio.strftime("%Y-%m-%d"),
                    fecha_fin.strftime("%Y-%m-%d")
                )

                # Procesar resultados paralelos
                for ticker, result in parallel_results:
                    if result is None:
                        print(f"No se pudo obtener datos para {ticker}. Saltando al siguiente.")
                        continue

                    datos_historicos = result['datos_historicos']
                    datos_con_indicadores = result['datos_con_indicadores']
                    resultado_analisis = result['resultado_analisis']
                    company_name = result['company_name']

                    # Add ticker column to datos_historicos before appending
                    datos_historicos['ticker'] = ticker
                    all_historical_data.append(datos_historicos)

                    # Preparar datos para la tabla usando utilidad
                    row_data = prepare_table_row(resultado_analisis, company_name, datos_con_indicadores)
                    all_results.append(row_data)

            else:
                print("Usando procesamiento secuencial...")
                for ticker in tickers:
                    print(f"--- Analizando {ticker} ---")

                    # 1. Adquisición de Datos
                    print("Descargando datos...")
                    datos_historicos, company_name = data_acquisition.descargar_datos(ticker, fecha_inicio.strftime("%Y-%m-%d"), fecha_fin.strftime("%Y-%m-%d"))

                    if datos_historicos is not None:
                        # Add ticker column to datos_historicos before appending
                        datos_historicos['ticker'] = ticker
                        all_historical_data.append(datos_historicos)

                        # 2. Almacenamiento de Datos
                        print("Guardando datos en la base de datos...")
                        data_storage.guardar_datos(datos_historicos, ticker)

                        # 3. Usar datos frescos descargados (no re-leer de base de datos)
                        print("Usando datos frescos descargados...")
                        datos_frescos = datos_historicos.copy()
                        datos_frescos['ticker'] = ticker # Añadir columna ticker

                        # 4. Cálculo de Indicadores Técnicos
                        print("Calculando indicadores técnicos...")
                        datos_con_indicadores = indicator_calculator.calcular_indicadores(datos_frescos)

                        # Asegurarse de que no haya valores NaN que afecten el análisis de señales
                        datos_con_indicadores.dropna(inplace=True)

                        if len(datos_con_indicadores) < 2:
                            print(f"No hay suficientes datos para generar señales para {ticker}.")
                            continue

                        # 5. Generación de Señales
                        print("Generando señales de trading...")
                        resultado_analisis = signal_generator.generar_senales(datos_con_indicadores)

                        # 6. Generación de Gráficos
                        print("Generando gráfico interactivo...")
                        visualizer.generar_grafico(datos_con_indicadores, resultado_analisis, ticker)

                        # Preparar datos para la tabla usando utilidad
                        row_data = prepare_table_row(resultado_analisis, company_name, datos_con_indicadores)
                        all_results.append(row_data)

                    else:
                        print(f"No se pudo obtener datos para {ticker}. Saltando al siguiente.")

            # --- CSV Export Logic ---
            if all_historical_data:
                full_historical_df = pd.concat(all_historical_data)
                
                data_types = CSV_DATA_TYPES

                salidas_dir = os.path.join(BASE_DIR, 'salidas')
                os.makedirs(salidas_dir, exist_ok=True) # Create the directory if it doesn't exist

                for original_col, csv_name in data_types.items():
                    print(f"Generando archivo CSV para {original_col}...")
                    # Select relevant columns and pivot
                    pivot_df = full_historical_df.pivot_table(
                        index='ticker',
                        columns='fecha',
                        values=original_col
                    )
                    # Save to CSV
                    csv_file_path = os.path.join(salidas_dir, f"{csv_name}_data.csv")
                    try:
                        pivot_df.to_csv(csv_file_path)
                        print(f"Archivo {csv_file_path} generado exitosamente.")

                        # --- NEW: Modify the CSV format ---
                        print(f"Modificando formato del archivo {csv_name}_data.csv para Excel...")
                        success, message = modify_csv_format(csv_file_path, csv_file_path) # Overwrite
                        if success:
                            print(f"Formato de {csv_name}_data.csv modificado exitosamente.")
                        else:
                            print(f"Error al modificar {csv_name}_data.csv: {message}")
                        # --- END NEW ---
                    except IOError as e:
                        print(f"Error al guardar el archivo CSV {csv_file_path}: {e}")

            else:
                print("No se encontraron datos históricos para exportar a CSV.")
            # --- End CSV Export Logic ---

            # Usar headers dinámicos
            headers = get_dynamic_table_headers()
            print("\n" + tabulate(all_results, headers=headers, tablefmt="grid"))

    except IOError as e:
        print(f"Error al escribir en el archivo de salida {salida_path}: {e}")
    finally:
        if 'f_salida' in locals() and not f_salida.closed:
            f_salida.close()
        sys.stdout = original_stdout # Restaurar la salida estándar

    print(f"Análisis completado. Verifique {salida_path} para los resultados.")
    salidas_dir = os.path.join(BASE_DIR, 'salidas') # Definir salidas_dir también fuera del bloque try
    print(f"Archivos CSV de datos históricos generados en la carpeta '{os.path.basename(salidas_dir)}'.")
    print(f"Archivos HTML con gráficos interactivos generados en la carpeta '{os.path.basename(salidas_dir)}'.")

if __name__ == "__main__":
    main()
