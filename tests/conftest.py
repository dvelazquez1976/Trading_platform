"""Fixtures compartidas para pytest."""

import os
import tempfile

import pandas as pd
import pytest


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    """DataFrame OHLCV con 100 sesiones simuladas."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="B")
    base = 10.0
    prices = [base + i * 0.1 + (i % 7) * 0.05 for i in range(100)]
    return pd.DataFrame({
        "fecha":    dates,
        "apertura": [p - 0.05 for p in prices],
        "maximo":   [p + 0.15 for p in prices],
        "minimo":   [p - 0.15 for p in prices],
        "cierre":   prices,
        "volumen":  [1_000_000 + i * 5_000 for i in range(100)],
    })


@pytest.fixture
def sample_ohlcv_with_indicators(sample_ohlcv) -> pd.DataFrame:
    """DataFrame con indicadores ya calculados."""
    from trading_platform.indicators.basic import calcular_indicadores
    df = calcular_indicadores(sample_ohlcv.copy())
    df.dropna(inplace=True)
    return df


@pytest.fixture
def temp_db(tmp_path) -> str:
    """Ruta a una base de datos SQLite temporal."""
    return str(tmp_path / "test.db")


@pytest.fixture
def temp_cache_dir(tmp_path) -> str:
    """Directorio temporal para caché."""
    return str(tmp_path / "cache")
