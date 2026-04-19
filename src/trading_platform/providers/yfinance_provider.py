"""Proveedor yfinance — fallback gratuito con buena cobertura US."""

from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf

from trading_platform.providers.base import DataProvider, ProviderError
from trading_platform.core.logging import get_logger

logger = get_logger(__name__)


class YFinanceProvider(DataProvider):
    name = "yfinance"
    is_free = True
    requires_api_key = False

    def fetch_ohlcv(self, ticker: str, start: date, end: date) -> Optional[pd.DataFrame]:
        logger.debug(f"[yfinance] descargando {ticker}")
        try:
            raw = yf.download(
                ticker,
                start=start.strftime('%Y-%m-%d'),
                end=end.strftime('%Y-%m-%d'),
                auto_adjust=True,
                progress=False
            )
        except Exception as e:
            raise ProviderError(f"yfinance error para {ticker}: {e}")

        if raw is None or raw.empty:
            raise ProviderError(f"yfinance sin datos para {ticker}")

        # Aplanar MultiIndex si existe
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.droplevel(1)

        raw.reset_index(inplace=True)

        col_map = {
            'Date': 'fecha', 'Open': 'apertura', 'High': 'maximo',
            'Low': 'minimo', 'Close': 'cierre', 'Volume': 'volumen',
            'Adj Close': 'cierre'
        }
        raw.rename(columns=col_map, inplace=True)

        required = ['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen']
        missing = [c for c in required if c not in raw.columns]
        if missing:
            raise ProviderError(f"yfinance columnas faltantes {ticker}: {missing}")

        df = raw[required].copy()
        df['fecha'] = pd.to_datetime(df['fecha'])
        df.dropna(subset=['cierre'], inplace=True)
        df.sort_values('fecha', inplace=True)
        df.reset_index(drop=True, inplace=True)

        logger.info(f"[yfinance] {ticker}: {len(df)} filas")
        return df

    def fetch_company_info(self, ticker: str) -> dict:
        try:
            info = yf.Ticker(ticker).info or {}
            return {
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'N/A'),
                'market_cap': info.get('marketCap'),
            }
        except Exception:
            return {'name': ticker, 'sector': 'N/A', 'market_cap': None}
