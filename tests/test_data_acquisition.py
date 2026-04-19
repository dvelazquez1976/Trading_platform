"""Tests para providers/ — usa datos sintéticos, sin red."""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from trading_platform.providers.stooq import StooqProvider, _yahoo_to_stooq
from trading_platform.providers.yfinance_provider import YFinanceProvider
from trading_platform.providers.base import ProviderError


class TestStooqTickerMapping:
    @pytest.mark.parametrize("yahoo,expected", [
        ("SAN.MC", "san.es"),
        ("BMW.DE", "bmw.de"),
        ("AZN.L",  "azn.uk"),
        ("MC.PA",  "mc.fr"),
        ("7203.T", "7203.jp"),
        ("AAPL",   "aapl"),
        ("BRK-B",  "brk_b"),
    ])
    def test_mapeo_sufijos(self, yahoo, expected):
        assert _yahoo_to_stooq(yahoo) == expected


class TestStooqProvider:
    def test_error_si_requiere_apikey(self):
        provider = StooqProvider()
        raw_apikey = "Get your apikey:\n\n1. Open https://stooq.com/q/d/?s=san.es"
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.read.return_value = raw_apikey.encode("utf-8")
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_open.return_value = mock_resp
            with pytest.raises(ProviderError, match="API key|apikey"):
                provider.fetch_ohlcv("SAN.MC", "2024-01-01", "2024-12-31")

    def test_error_si_sin_datos(self):
        provider = StooqProvider()
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b"No data"
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_open.return_value = mock_resp
            with pytest.raises(ProviderError):
                provider.fetch_ohlcv("ZZZZ", "2024-01-01", "2024-12-31")


class TestOrchestrator:
    def test_fallback_a_segundo_proveedor(self, sample_ohlcv):
        from trading_platform.providers.orchestrator import DataOrchestrator
        from trading_platform.providers.base import ProviderError

        p1 = MagicMock()
        p1.name = "falla"
        p1.supports.return_value = True
        p1.fetch_ohlcv.side_effect = ProviderError("fallo simulado")

        p2 = MagicMock()
        p2.name = "ok"
        p2.supports.return_value = True
        p2.fetch_ohlcv.return_value = sample_ohlcv

        orch = DataOrchestrator(providers=[p1, p2])
        result = orch.fetch_ohlcv("TEST", "2024-01-01", "2024-12-31")
        assert result is not None
        assert len(result) == len(sample_ohlcv)
