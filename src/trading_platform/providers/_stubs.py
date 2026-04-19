"""
Stubs de proveedores de pago — esqueletos listos para activar.

Activar un proveedor cuando quieras pagar:
    1. Crea cuenta y obtén API key en el proveedor.
    2. Añade la key en ⚙️ Configuración → Proveedores → API Keys.
    3. Implementa los métodos marcados con TODO en la clase correspondiente.
    4. Añade el proveedor al inicio de la cadena en DataOrchestrator.

No se necesita tocar ningún otro fichero del proyecto.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd

from trading_platform.providers.base import DataProvider, ProviderError


# ──────────────────────────────────────────────────────────────
# Financial Modeling Prep (FMP)
# https://financialmodelingprep.com/developer/docs/
# Plan mínimo útil: Starter (~22 USD/mes) — fundamentales históricos,
# ratings, earnings, dividendos para mercados globales.
# ──────────────────────────────────────────────────────────────
class FMPProvider(DataProvider):
    """
    Financial Modeling Prep — fundamentales premium y OHLCV global.

    Cuando implementes:
        - fetch_ohlcv  → GET /historical-price-full/{ticker}?from=...&to=...&apikey=...
        - fetch_company_info → GET /profile/{ticker}?apikey=...
    """

    name = "fmp"
    is_free = False
    requires_api_key = True

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def fetch_ohlcv(self, ticker: str, start: date, end: date) -> Optional[pd.DataFrame]:
        # TODO: implementar cuando tengas plan FMP activo
        # Endpoint: https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}
        # Columnas respuesta: date, open, high, low, close, volume
        # Mapear a: fecha, apertura, maximo, minimo, cierre, volumen
        raise NotImplementedError(
            "FMPProvider no está implementado. "
            "Consulta los comentarios en providers/_stubs.py para activarlo."
        )

    def fetch_company_info(self, ticker: str) -> dict:
        # TODO: implementar cuando tengas plan FMP activo
        # Endpoint: https://financialmodelingprep.com/api/v3/profile/{ticker}
        raise NotImplementedError("FMPProvider.fetch_company_info no implementado.")

    def supports(self, ticker: str) -> bool:
        return bool(self.api_key)  # solo activo si hay key configurada


# ──────────────────────────────────────────────────────────────
# EOD Historical Data (EODHD)
# https://eodhd.com/
# Plan All-World (~19.99 USD/mes) — OHLCV para 70+ mercados,
# dividendos y splits precisos, forex, cripto.
# ──────────────────────────────────────────────────────────────
class EODHDProvider(DataProvider):
    """
    EOD Historical Data — cobertura global, dividendos precisos.

    Cuando implementes:
        - fetch_ohlcv → GET /api/eod/{ticker}.{exchange}?from=...&to=...&api_token=...&fmt=json
        - El ticker IBEX en EODHD usa sufijo .MC, igual que Yahoo Finance.
    """

    name = "eodhd"
    is_free = False
    requires_api_key = True

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def fetch_ohlcv(self, ticker: str, start: date, end: date) -> Optional[pd.DataFrame]:
        # TODO: implementar cuando tengas plan EODHD activo
        # Endpoint: https://eodhd.com/api/eod/{ticker}
        # Columnas respuesta: date, open, high, low, close, adjusted_close, volume
        # Usar adjusted_close como cierre para precios ajustados por splits/dividendos
        raise NotImplementedError(
            "EODHDProvider no está implementado. "
            "Consulta los comentarios en providers/_stubs.py para activarlo."
        )

    def fetch_company_info(self, ticker: str) -> dict:
        # TODO: implementar cuando tengas plan EODHD activo
        # Endpoint: https://eodhd.com/api/fundamentals/{ticker}
        raise NotImplementedError("EODHDProvider.fetch_company_info no implementado.")

    def supports(self, ticker: str) -> bool:
        return bool(self.api_key)


# ──────────────────────────────────────────────────────────────
# Polygon.io
# https://polygon.io/
# Starter (~29 USD/mes) — datos US en tiempo real (15 min delay free),
# opciones, forex, cripto. Mercados europeos solo en plan superior.
# ──────────────────────────────────────────────────────────────
class PolygonProvider(DataProvider):
    """
    Polygon.io — real-time US, opciones, cripto.

    Nota: mercados europeos (IBEX, DAX...) requieren plan Business o superior.
    Recomendado solo si el foco es S&P 500 / NASDAQ.

    Cuando implementes:
        - fetch_ohlcv → GET /v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}?apiKey=...
        - Tickers US sin sufijo (AAPL, MSFT). Para ETFs: SPY, QQQ.
    """

    name = "polygon"
    is_free = False
    requires_api_key = True
    supported_suffixes: tuple = ()  # solo tickers sin sufijo (US)

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def fetch_ohlcv(self, ticker: str, start: date, end: date) -> Optional[pd.DataFrame]:
        # TODO: implementar cuando tengas plan Polygon activo
        # Endpoint: https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}
        # Columnas respuesta: t (timestamp ms), o, h, l, c, v
        # Convertir t → fecha con pd.to_datetime(df['t'], unit='ms').dt.date
        raise NotImplementedError(
            "PolygonProvider no está implementado. "
            "Consulta los comentarios en providers/_stubs.py para activarlo."
        )

    def fetch_company_info(self, ticker: str) -> dict:
        # TODO: implementar cuando tengas plan Polygon activo
        # Endpoint: https://api.polygon.io/v3/reference/tickers/{ticker}
        raise NotImplementedError("PolygonProvider.fetch_company_info no implementado.")

    def supports(self, ticker: str) -> bool:
        # Solo tickers US (sin punto en el nombre)
        return bool(self.api_key) and "." not in ticker


# ──────────────────────────────────────────────────────────────
# Finnhub
# https://finnhub.io/
# Free: 60 req/min para US. EU requiere plan pago.
# Útil para: earnings calendar, news, estimaciones consensus.
# ──────────────────────────────────────────────────────────────
class FinnhubProvider(DataProvider):
    """
    Finnhub — earnings calendar, news y sentimiento (US principalmente).

    No recomendado como proveedor OHLCV principal (límites bajos, cobertura EU limitada).
    Mejor uso: datos complementarios (noticias, earnings) para tickers US.

    Cuando implementes:
        - fetch_ohlcv → GET /stock/candle?symbol={ticker}&resolution=D&from={ts}&to={ts}&token=...
        - Timestamps UNIX (segundos). from/to se calculan con int(datetime.timestamp()).
    """

    name = "finnhub"
    is_free = False
    requires_api_key = True

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def fetch_ohlcv(self, ticker: str, start: date, end: date) -> Optional[pd.DataFrame]:
        # TODO: implementar cuando tengas API key de Finnhub
        # Endpoint: https://finnhub.io/api/v1/stock/candle
        # Params: symbol, resolution='D', from=unix_ts, to=unix_ts, token=api_key
        # Columnas respuesta: t[], o[], h[], l[], c[], v[]
        raise NotImplementedError(
            "FinnhubProvider no está implementado. "
            "Consulta los comentarios en providers/_stubs.py para activarlo."
        )

    def fetch_company_info(self, ticker: str) -> dict:
        # TODO: GET https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token=...
        raise NotImplementedError("FinnhubProvider.fetch_company_info no implementado.")

    def supports(self, ticker: str) -> bool:
        return bool(self.api_key) and "." not in ticker  # principalmente US
