"""Proveedor Stooq — gratuito, sin API key, excelente cobertura global y IBEX."""

from datetime import date
from typing import Optional
import io

import pandas as pd
import urllib.request
import urllib.error

from trading_platform.providers.base import DataProvider, ProviderError
from trading_platform.core.logging import get_logger

logger = get_logger(__name__)


# Mapa de sufijos Yahoo → Stooq
_SUFFIX_MAP = {
    '.MC': '.es',  # IBEX 35
    '.DE': '.de',  # DAX
    '.PA': '.fr',  # CAC 40
    '.L':  '.uk',  # FTSE 100
    '.T':  '.jp',  # Nikkei
    '.AS': '.nl',  # AEX
    '.MI': '.it',  # FTSE MIB
}


def _yahoo_to_stooq(ticker: str) -> str:
    """Convierte ticker Yahoo Finance a formato Stooq."""
    for yf_suffix, stooq_suffix in _SUFFIX_MAP.items():
        if ticker.upper().endswith(yf_suffix.upper()):
            base = ticker[:len(ticker) - len(yf_suffix)]
            return (base + stooq_suffix).lower()
    # US stocks: sin sufijo o con .US
    return ticker.lower().replace('-', '_')


class StooqProvider(DataProvider):
    name = "stooq"
    is_free = True
    requires_api_key = False
    supported_suffixes = ()  # soporta todo

    def fetch_ohlcv(self, ticker: str, start: date, end: date) -> Optional[pd.DataFrame]:
        stooq_ticker = _yahoo_to_stooq(ticker)
        url = (
            f"https://stooq.com/q/d/l/?s={stooq_ticker}"
            f"&d1={start.strftime('%Y%m%d')}&d2={end.strftime('%Y%m%d')}&i=d"
        )
        logger.debug(f"[Stooq] GET {url}")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode('utf-8')
        except urllib.error.URLError as e:
            raise ProviderError(f"Stooq error de red para {ticker}: {e}")

        if 'No data' in raw or len(raw.strip()) < 50:
            raise ProviderError(f"Stooq sin datos para {ticker}")

        try:
            df = pd.read_csv(io.StringIO(raw))
        except Exception as e:
            raise ProviderError(f"Stooq error parseando CSV para {ticker}: {e}")

        # Normalizar columnas
        df.columns = [c.strip() for c in df.columns]
        col_map = {
            'Date': 'fecha', 'Open': 'apertura', 'High': 'maximo',
            'Low': 'minimo', 'Close': 'cierre', 'Volume': 'volumen'
        }
        df.rename(columns=col_map, inplace=True)

        required = ['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen']
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ProviderError(f"Stooq columnas inesperadas para {ticker}: {missing}")

        df = df[required].copy()
        df['fecha'] = pd.to_datetime(df['fecha'])
        df.dropna(subset=['cierre'], inplace=True)
        df.sort_values('fecha', inplace=True)
        df.reset_index(drop=True, inplace=True)

        logger.info(f"[Stooq] {ticker}: {len(df)} filas descargadas")
        return df

    def fetch_company_info(self, ticker: str) -> dict:
        # Stooq no expone info de empresa fácilmente — devolvemos mínimo
        return {'name': ticker, 'sector': 'N/A', 'market_cap': None}
