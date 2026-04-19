"""Tests para storage/database.py y storage/cache.py."""

import pandas as pd
import pytest

from trading_platform.storage.database import crear_base_de_datos, guardar_datos
from trading_platform.storage.cache import CacheManager


class TestDatabase:
    def test_crear_y_guardar(self, sample_ohlcv, temp_db):
        crear_base_de_datos(db_path=temp_db)
        sample_ohlcv["ticker"] = "TEST"
        guardar_datos(sample_ohlcv, "TEST", db_path=temp_db)

    def test_guardar_multiples_tickers(self, sample_ohlcv, temp_db):
        crear_base_de_datos(db_path=temp_db)
        for t in ["AAA", "BBB"]:
            df = sample_ohlcv.copy()
            df["ticker"] = t
            guardar_datos(df, t, db_path=temp_db)

    def test_guardar_df_vacio_no_falla(self, temp_db):
        crear_base_de_datos(db_path=temp_db)
        empty = pd.DataFrame(columns=["fecha", "apertura", "maximo", "minimo", "cierre", "volumen", "ticker"])
        guardar_datos(empty, "EMPTY", db_path=temp_db)


class TestCache:
    def test_set_get(self, temp_cache_dir, sample_ohlcv):
        cache = CacheManager(cache_dir=temp_cache_dir)
        cache.set("TEST", "2024-01-01", "2024-12-31", sample_ohlcv, "Test Corp")
        result = cache.get("TEST", "2024-01-01", "2024-12-31")
        assert result is not None
        df, name = result
        assert len(df) == len(sample_ohlcv)
        assert name == "Test Corp"

    def test_miss_devuelve_none(self, temp_cache_dir):
        cache = CacheManager(cache_dir=temp_cache_dir)
        assert cache.get("NOEXISTE", "2020-01-01", "2020-12-31") is None

    def test_limpiar(self, temp_cache_dir, sample_ohlcv):
        cache = CacheManager(cache_dir=temp_cache_dir)
        cache.set("TEST", "2024-01-01", "2024-12-31", sample_ohlcv, "Test Corp")
        cache.invalidate("TEST", "2024-01-01", "2024-12-31")
        assert cache.get("TEST", "2024-01-01", "2024-12-31") is None
