"""Utilidades comunes para la plataforma de trading."""

import pandas as pd
from typing import Dict, Any
from constants import COLUMN_MAPPING_ES_EN, COLUMN_MAPPING_EN_ES, YFINANCE_COLUMN_MAPPING

def rename_columns_to_english(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renombra las columnas de español a inglés para compatibilidad con pandas_ta.

    Args:
        df: DataFrame con columnas en español

    Returns:
        DataFrame con columnas en inglés
    """
    df_copy = df.copy()
    df_copy.rename(columns=COLUMN_MAPPING_ES_EN, inplace=True)
    return df_copy

def rename_columns_to_spanish(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renombra las columnas de inglés a español.

    Args:
        df: DataFrame con columnas en inglés

    Returns:
        DataFrame con columnas en español
    """
    df_copy = df.copy()
    df_copy.rename(columns=COLUMN_MAPPING_EN_ES, inplace=True)
    return df_copy

def rename_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renombra las columnas de Yahoo Finance al formato español estándar.

    Args:
        df: DataFrame con columnas de Yahoo Finance

    Returns:
        DataFrame con columnas en español
    """
    df_copy = df.copy()
    df_copy.rename(columns=YFINANCE_COLUMN_MAPPING, inplace=True)
    return df_copy

def validate_required_columns(df: pd.DataFrame, required_columns: list) -> bool:
    """
    Valida que el DataFrame contenga todas las columnas requeridas.

    Args:
        df: DataFrame a validar
        required_columns: Lista de columnas requeridas

    Returns:
        True si todas las columnas están presentes, False en caso contrario
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Faltan columnas requeridas: {missing_columns}")
    return True

def format_price(price: float, decimals: int = 2) -> str:
    """
    Formatea un precio con el número especificado de decimales.

    Args:
        price: Precio a formatear
        decimals: Número de decimales

    Returns:
        Precio formateado como string
    """
    return f"{price:.{decimals}f}"

def safe_get_last_value(df: pd.DataFrame, column: str, default=0.0) -> Any:
    """
    Obtiene de forma segura el último valor de una columna.

    Args:
        df: DataFrame
        column: Nombre de la columna
        default: Valor por defecto si la columna no existe o está vacía

    Returns:
        Último valor de la columna o valor por defecto
    """
    try:
        if column not in df.columns:
            return default
        if df.empty:
            return default
        return df[column].iloc[-1]
    except (IndexError, KeyError):
        return default

def prepare_table_row(resultado_analisis: Dict[str, Any], company_name: str,
                     datos_con_indicadores: pd.DataFrame) -> list:
    """
    Prepara una fila para la tabla de resultados.

    Args:
        resultado_analisis: Diccionario con resultados del análisis
        company_name: Nombre de la empresa
        datos_con_indicadores: DataFrame con indicadores calculados

    Returns:
        Lista con datos de la fila
    """
    from constants import AVAILABLE_INDICATORS, INDICATOR_RESULT_COLUMNS, ADVANCED_INDICATORS, ADVANCED_INDICATOR_COLUMNS
    from advanced_signals import get_advanced_indicator_values
    from config_manager import config_manager

    row_data = [
        resultado_analisis["ticker"],
        company_name,
        resultado_analisis["fecha"],
        format_price(resultado_analisis["precio_cierre"]),
        resultado_analisis["resumen"]
    ]

    # Añadir señales de indicadores básicos
    for indicator in AVAILABLE_INDICATORS:
        if indicator in resultado_analisis["señales"]:
            row_data.append(resultado_analisis["señales"][indicator])
        else:
            row_data.append("KEEP/NO SIGNAL")

    # Añadir señales de indicadores avanzados si están habilitados
    advanced_config = config_manager.get('advanced_indicators', default={})
    if advanced_config.get('enabled', False):
        for indicator in ADVANCED_INDICATORS:
            if indicator in resultado_analisis["señales"]:
                row_data.append(resultado_analisis["señales"][indicator])
            else:
                row_data.append("KEEP/NO SIGNAL")

    # Añadir valores de indicadores básicos
    if not datos_con_indicadores.empty:
        last_row = datos_con_indicadores.iloc[-1]
        for column in INDICATOR_RESULT_COLUMNS:
            value = safe_get_last_value(datos_con_indicadores, column)
            if isinstance(value, (int, float)):
                row_data.append(format_price(value))
            else:
                row_data.append(str(value))

        # Añadir valores de indicadores avanzados si están habilitados
        if advanced_config.get('enabled', False):
            advanced_values = get_advanced_indicator_values(datos_con_indicadores)
            for column in ADVANCED_INDICATOR_COLUMNS:
                if column in advanced_values:
                    value = advanced_values[column]
                    if isinstance(value, (int, float)):
                        row_data.append(format_price(value))
                    else:
                        row_data.append(str(value))
                else:
                    row_data.append("N/A")
    else:
        # Si no hay datos, llenar con valores por defecto
        total_columns = len(INDICATOR_RESULT_COLUMNS)
        if advanced_config.get('enabled', False):
            total_columns += len(ADVANCED_INDICATOR_COLUMNS)
        row_data.extend(["N/A"] * total_columns)

    return row_data

def validate_ticker(ticker: str) -> bool:
    """
    Valida que el ticker sea válido.

    Args:
        ticker: Ticker a validar

    Returns:
        True si el ticker es válido
    """
    if not ticker or not isinstance(ticker, str):
        raise ValueError("El ticker debe ser una cadena no vacía")

    if len(ticker.strip()) == 0:
        raise ValueError("El ticker no puede estar vacío")

    return True

def validate_date_format(date_str: str) -> bool:
    """
    Valida que la fecha tenga formato correcto.

    Args:
        date_str: Fecha en formato string

    Returns:
        True si la fecha es válida
    """
    try:
        pd.to_datetime(date_str)
        return True
    except ValueError as e:
        raise ValueError(f"Formato de fecha inválido: {e}")

def get_dynamic_table_headers() -> list:
    """
    Construye dinámicamente los headers de la tabla según la configuración.

    Returns:
        Lista de headers para la tabla
    """
    from constants import BASE_TABLE_HEADERS, AVAILABLE_INDICATORS, INDICATOR_RESULT_COLUMNS, ADVANCED_INDICATORS, ADVANCED_INDICATOR_COLUMNS
    from config_manager import config_manager

    headers = BASE_TABLE_HEADERS.copy()
    headers.extend(AVAILABLE_INDICATORS)

    # Añadir headers de indicadores avanzados si están habilitados
    advanced_config = config_manager.get('advanced_indicators', default={})
    if advanced_config.get('enabled', False):
        headers.extend(ADVANCED_INDICATORS)

    # Añadir headers de valores de indicadores
    headers.extend(INDICATOR_RESULT_COLUMNS)

    if advanced_config.get('enabled', False):
        headers.extend(ADVANCED_INDICATOR_COLUMNS)

    return headers

def clean_dataframe(df: pd.DataFrame, drop_na: bool = True) -> pd.DataFrame:
    """
    Limpia un DataFrame eliminando NaN y filas inválidas.

    Args:
        df: DataFrame a limpiar
        drop_na: Si eliminar filas con NaN

    Returns:
        DataFrame limpio
    """
    df_clean = df.copy()

    if drop_na:
        df_clean.dropna(inplace=True)

    return df_clean

def prepare_summary_table_row(resultado_analisis: Dict[str, Any], company_name: str) -> list:
    """
    Prepara una fila para la tabla resumen (información general).

    Args:
        resultado_analisis: Diccionario con resultados del análisis
        company_name: Nombre de la empresa

    Returns:
        Lista con datos básicos de la fila
    """
    return [
        resultado_analisis["ticker"],
        company_name,
        resultado_analisis["fecha"],
        format_price(resultado_analisis["precio_cierre"]),
        resultado_analisis["resumen"]
    ]

def prepare_signals_table_row(resultado_analisis: Dict[str, Any], basic: bool = True) -> list:
    """
    Prepara una fila para la tabla de señales.

    Args:
        resultado_analisis: Diccionario con resultados del análisis
        basic: True para indicadores básicos, False para avanzados

    Returns:
        Lista con señales de indicadores
    """
    from constants import AVAILABLE_INDICATORS, ADVANCED_INDICATORS

    row_data = [resultado_analisis["ticker"]]

    indicators = AVAILABLE_INDICATORS if basic else ADVANCED_INDICATORS

    for indicator in indicators:
        if indicator in resultado_analisis["señales"]:
            row_data.append(resultado_analisis["señales"][indicator])
        else:
            row_data.append("KEEP/NO SIGNAL")

    return row_data

def prepare_values_table_row(resultado_analisis: Dict[str, Any],
                             datos_con_indicadores: pd.DataFrame,
                             basic: bool = True) -> list:
    """
    Prepara una fila para la tabla de valores de indicadores.

    Args:
        resultado_analisis: Diccionario con resultados del análisis
        datos_con_indicadores: DataFrame con indicadores calculados
        basic: True para indicadores básicos, False para avanzados

    Returns:
        Lista con valores de indicadores
    """
    from constants import INDICATOR_RESULT_COLUMNS, ADVANCED_INDICATOR_COLUMNS
    from advanced_signals import get_advanced_indicator_values

    row_data = [resultado_analisis["ticker"]]

    if basic:
        # Valores de indicadores básicos
        columns = INDICATOR_RESULT_COLUMNS
        if not datos_con_indicadores.empty:
            for column in columns:
                value = safe_get_last_value(datos_con_indicadores, column)
                if isinstance(value, (int, float)):
                    row_data.append(format_price(value))
                else:
                    row_data.append(str(value))
        else:
            row_data.extend(["N/A"] * len(columns))
    else:
        # Valores de indicadores avanzados
        columns = ADVANCED_INDICATOR_COLUMNS
        if not datos_con_indicadores.empty:
            advanced_values = get_advanced_indicator_values(datos_con_indicadores)
            for column in columns:
                if column in advanced_values:
                    value = advanced_values[column]
                    if isinstance(value, (int, float)):
                        row_data.append(format_price(value))
                    else:
                        row_data.append(str(value))
                else:
                    row_data.append("N/A")
        else:
            row_data.extend(["N/A"] * len(columns))

    return row_data

def get_summary_table_headers() -> list:
    """Retorna los headers para la tabla resumen."""
    from constants import BASE_TABLE_HEADERS
    return BASE_TABLE_HEADERS.copy()

def get_signals_table_headers(basic: bool = True) -> list:
    """
    Retorna los headers para la tabla de señales.

    Args:
        basic: True para indicadores básicos, False para avanzados
    """
    from constants import AVAILABLE_INDICATORS, ADVANCED_INDICATORS

    indicators = AVAILABLE_INDICATORS if basic else ADVANCED_INDICATORS
    return ["Ticker"] + indicators

def get_values_table_headers(basic: bool = True) -> list:
    """
    Retorna los headers para la tabla de valores.

    Args:
        basic: True para indicadores básicos, False para avanzados
    """
    from constants import INDICATOR_RESULT_COLUMNS, ADVANCED_INDICATOR_COLUMNS

    columns = INDICATOR_RESULT_COLUMNS if basic else ADVANCED_INDICATOR_COLUMNS
    return ["Ticker"] + columns