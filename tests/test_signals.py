"""Tests para signals/generator.py."""

import pytest

from trading_platform.signals.generator import generar_senales


class TestGenerarSenales:
    def test_estructura_resultado(self, sample_ohlcv_with_indicators):
        res = generar_senales(sample_ohlcv_with_indicators)
        assert "ticker" in res
        assert "resumen" in res
        assert "señales" in res
        assert "precio_cierre" in res
        assert "fecha" in res

    def test_resumen_valido(self, sample_ohlcv_with_indicators):
        res = generar_senales(sample_ohlcv_with_indicators)
        assert res["resumen"] in ("COMPRA", "VENTA", "KEEP/NO SIGNAL")

    def test_senales_valores_validos(self, sample_ohlcv_with_indicators):
        res = generar_senales(sample_ohlcv_with_indicators)
        valores_validos = {"COMPRA", "VENTA", "KEEP/NO SIGNAL"}
        for ind, val in res["señales"].items():
            assert val in valores_validos, f"{ind} tiene valor inesperado: {val}"

    def test_precio_positivo(self, sample_ohlcv_with_indicators):
        res = generar_senales(sample_ohlcv_with_indicators)
        assert res["precio_cierre"] > 0
