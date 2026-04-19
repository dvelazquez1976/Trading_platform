"""Utilidades comunes."""

import re
import pandas as pd
from typing import Any, Dict

from trading_platform.core.constants import (
    COLUMN_MAPPING_ES_EN, COLUMN_MAPPING_EN_ES, YFINANCE_COLUMN_MAPPING,
    AVAILABLE_INDICATORS, ADVANCED_INDICATORS,
    INDICATOR_RESULT_COLUMNS, ADVANCED_INDICATOR_COLUMNS, BASE_TABLE_HEADERS
)


# ── Column rename helpers ──────────────────────────────────────────────────

def rename_columns_to_english(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy().rename(columns=COLUMN_MAPPING_ES_EN)

def rename_columns_to_spanish(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy().rename(columns=COLUMN_MAPPING_EN_ES)

def rename_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy().rename(columns=YFINANCE_COLUMN_MAPPING)


# ── Validation ─────────────────────────────────────────────────────────────

def validate_required_columns(df: pd.DataFrame, required: list) -> bool:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas: {missing}")
    return True

def validate_ticker(ticker: str) -> bool:
    if not ticker or not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("Ticker inválido o vacío")
    return True

def validate_date_format(date_str: str) -> bool:
    try:
        pd.to_datetime(date_str)
        return True
    except ValueError as e:
        raise ValueError(f"Fecha inválida: {e}")


# ── Formatting ─────────────────────────────────────────────────────────────

def format_price(price: float, decimals: int = 2) -> str:
    return f"{price:.{decimals}f}"

def safe_get_last_value(df: pd.DataFrame, column: str, default=0.0) -> Any:
    try:
        return df[column].iloc[-1] if column in df.columns and not df.empty else default
    except (IndexError, KeyError):
        return default


# ── CSV formatter (formerly csv_formatter.py) ─────────────────────────────

def modify_csv_format(input_filepath: str, output_filepath: str):
    """Convierte CSV con separador ',' y decimal '.' al formato ';' y ',' (Excel ES)."""
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.readlines()
        modified = []
        for line in content:
            tmp = line.replace(',', '|')
            tmp = re.sub(r'(\d+)\.(\d+)', r'\1,\2', tmp)
            modified.append(tmp.replace('|', ';'))
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.writelines(modified)
        return True, "OK"
    except FileNotFoundError:
        return False, f"Fichero no encontrado: {input_filepath}"
    except Exception as e:
        return False, str(e)


# ── Table row builders ─────────────────────────────────────────────────────

def prepare_summary_table_row(resultado: Dict, company_name: str) -> list:
    return [
        resultado["ticker"], company_name, resultado["fecha"],
        format_price(resultado["precio_cierre"]), resultado["resumen"]
    ]

def prepare_signals_table_row(resultado: Dict, basic: bool = True) -> list:
    indicators = AVAILABLE_INDICATORS if basic else ADVANCED_INDICATORS
    row = [resultado["ticker"]]
    for ind in indicators:
        row.append(resultado["señales"].get(ind, "KEEP/NO SIGNAL"))
    return row

def prepare_values_table_row(resultado: Dict, datos: pd.DataFrame, basic: bool = True) -> list:
    from trading_platform.signals.advanced import get_advanced_indicator_values
    columns = INDICATOR_RESULT_COLUMNS if basic else ADVANCED_INDICATOR_COLUMNS
    row = [resultado["ticker"]]
    if basic:
        for col in columns:
            val = safe_get_last_value(datos, col)
            row.append(format_price(val) if isinstance(val, float) else str(val))
    else:
        adv = get_advanced_indicator_values(datos)
        for col in columns:
            val = adv.get(col, "N/A")
            row.append(format_price(val) if isinstance(val, float) else str(val))
    return row

def get_summary_table_headers() -> list:
    return BASE_TABLE_HEADERS.copy()

def get_signals_table_headers(basic: bool = True) -> list:
    indicators = AVAILABLE_INDICATORS if basic else ADVANCED_INDICATORS
    return ["Ticker"] + indicators

def get_values_table_headers(basic: bool = True) -> list:
    cols = INDICATOR_RESULT_COLUMNS if basic else ADVANCED_INDICATOR_COLUMNS
    return ["Ticker"] + cols
