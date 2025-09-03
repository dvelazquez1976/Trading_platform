import data_acquisition
import data_storage
import indicator_calculator
import signal_generator
import visualizer
from csv_formatter import modify_csv_format
import datetime
import json
import sys
import pandas as pd
from tabulate import tabulate
import os

# Definir el directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    """Flujo de ejecución principal del sistema de análisis de trading."""
    # Crear el directorio de salidas si no existe
    salidas_dir = os.path.join(BASE_DIR, 'salidas')
    os.makedirs(salidas_dir, exist_ok=True)

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

            # Definir el rango de fechas para el análisis (ej. los últimos 2 años)
            fecha_fin = datetime.date.today()
            fecha_inicio = fecha_fin - datetime.timedelta(days=2 * 365)

            all_results = []
            all_historical_data = [] # To collect all historical data for CSV export

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

                    # 3. Cargar Datos desde la Base de Datos
                    print("Cargando datos desde la base de datos...")
                    datos_desde_db = data_storage.leer_datos(ticker)
                    datos_desde_db['ticker'] = ticker # Añadir columna ticker

                    # 4. Cálculo de Indicadores Técnicos
                    print("Calculando indicadores técnicos...")
                    datos_con_indicadores = indicator_calculator.calcular_indicadores(datos_desde_db)
                    
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
                    visualizer.generar_grafico(datos_con_indicadores, resultado_analisis, ticker, salidas_dir)

                    # Preparar datos para la tabla
                    row_data = [
                        resultado_analisis["ticker"],
                        company_name, # Nombre de la empresa
                        resultado_analisis["fecha"],
                        f"{resultado_analisis["precio_cierre"]:.2f}",
                        resultado_analisis["resumen"] # Añadir el resumen de la recomendación
                    ]
                    for indicator in ["Cruce_Medias", "RSI", "Estocastico", "MACD", "Bandas_Bollinger", "Williams_R", "Awesome_Oscillator", "ROC"]:
                        row_data.append(resultado_analisis["señales"][indicator])
                    
                    # Añadir los últimos valores de los indicadores a la tabla
                    # Añadir los últimos valores de los indicadores a la tabla
                                        # Añadir los últimos valores de los indicadores a la tabla
                    last_row = datos_con_indicadores.iloc[-1]
                    row_data.append(f"{last_row['SMA_30']:.2f}")
                    row_data.append(f"{last_row['RSI_14']:.2f}")
                    row_data.append(f"{last_row['STOCHk_14_3_3']:.2f}")
                    row_data.append(f"{last_row['MACD_12_26_9']:.2f}")
                    row_data.append(f"{last_row['BBM_20_2']:.2f}")
                    row_data.append(f"{last_row['CCI_20_0.015']:.2f}")
                    row_data.append(f"{last_row['ADX_14']:.2f}")
                    row_data.append(f"{last_row['MFI_14']:.2f}")
                    row_data.append(f"{last_row['WILLR_14']:.2f}")
                    row_data.append(f"{last_row['AO_5_34']:.2f}")
                    row_data.append(f"{last_row['ROC_12']:.2f}")

                    all_results.append(row_data)

                else:
                    print(f"No se pudo obtener datos para {ticker}. Saltando al siguiente.")

            # --- CSV Export Logic ---
            if all_historical_data:
                full_historical_df = pd.concat(all_historical_data)
                
                data_types = {
                    'apertura': 'open',
                    'maximo': 'high',
                    'minimo': 'low',
                    'cierre': 'close',
                    'volumen': 'volume'
                }

                

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

            headers = ["Ticker", "Empresa", "Fecha", "Precio Cierre", "Recomendación", "Cruce Medias", "RSI", "Estocastico", "MACD", "Bandas Bollinger", "Williams %R", "Awesome Osc", "ROC", "SMA_30", "RSI_14", "STOCHk_14_3_3", "MACD_12_26_9", "BBM_20_2", "CCI_20_0.015", "ADX_14", "MFI_14", "WILLR_14", "AO_5_34", "ROC_12"]
            print("\n" + tabulate(all_results, headers=headers, tablefmt="grid"))

    except IOError as e:
        print(f"Error al escribir en el archivo de salida {salida_path}: {e}")
    finally:
        if 'f_salida' in locals() and not f_salida.closed:
            f_salida.close()
        sys.stdout = original_stdout # Restaurar la salida estándar

    print(f"Análisis completado. Verifique {salida_path} para los resultados.")
    print(f"Archivos CSV de datos históricos generados en la carpeta '{os.path.basename(salidas_dir)}'.")
    print(f"Archivos HTML con gráficos interactivos generados en la carpeta '{os.path.basename(salidas_dir)}'.")

if __name__ == "__main__":
    main()
