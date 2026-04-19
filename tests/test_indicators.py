"""Tests para indicators/basic.py."""

import pandas as pd
import pytest

from trading_platform.indicators.basic import calcular_indicadores


class TestCalcularIndicadores:
    def test_columnas_basicas(self, sample_ohlcv):
        df = calcular_indicadores(sample_ohlcv.copy())
        for col in ["SMA_30", "SMA_60", "SMA_90", "RSI", "MACD", "MACDs", "MACDh", "WILLR"]:
            assert col in df.columns, f"Falta columna {col}"

    def test_bollinger_presente(self, sample_ohlcv):
        df = calcular_indicadores(sample_ohlcv.copy())
        assert "BBU_BB" in df.columns
        assert "BBL_BB" in df.columns

    def test_no_elimina_filas(self, sample_ohlcv):
        df = calcular_indicadores(sample_ohlcv.copy())
        assert len(df) == len(sample_ohlcv)

    def test_rsi_rango(self, sample_ohlcv):
        df = calcular_indicadores(sample_ohlcv.copy()).dropna()
        assert (df["RSI"] >= 0).all() and (df["RSI"] <= 100).all()

    def test_sma_monotona_en_tendencia(self, sample_ohlcv):
        """SMA_30 debe ser creciente cuando el precio sube constantemente."""
        df = calcular_indicadores(sample_ohlcv.copy()).dropna()
        diffs = df["SMA_30"].diff().dropna()
        assert (diffs >= 0).all()
