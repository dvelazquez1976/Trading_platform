"""DataOrchestrator — cadena de proveedores con fallback automático."""

from datetime import date
from typing import Optional, Tuple, List

import pandas as pd

from trading_platform.providers.base import DataProvider, ProviderError, AllProvidersFailed
from trading_platform.providers.stooq import StooqProvider
from trading_platform.providers.yfinance_provider import YFinanceProvider
from trading_platform.core.logging import get_logger

logger = get_logger(__name__)


class DataOrchestrator:
    """
    Intenta proveedores en orden hasta obtener datos.
    Permite inyectar proveedores externos para extensión futura.
    """

    def __init__(self, providers: List[DataProvider] = None):
        # yfinance primario: Stooq ahora requiere API key (captcha en stooq.com)
        self.providers = providers or [YFinanceProvider(), StooqProvider()]

    def fetch_ohlcv(self, ticker: str, start: date, end: date) -> pd.DataFrame:
        errors = []
        for p in self.providers:
            if not p.supports(ticker):
                continue
            try:
                df = p.fetch_ohlcv(ticker, start, end)
                if df is not None and not df.empty:
                    return df
            except ProviderError as e:
                logger.warning(f"[{p.name}] fallo para {ticker}: {e}")
                errors.append(str(e))

        raise AllProvidersFailed(f"Todos los proveedores fallaron para {ticker}: {errors}")

    def fetch_company_info(self, ticker: str) -> dict:
        for p in self.providers:
            try:
                info = p.fetch_company_info(ticker)
                if info and info.get('name') != ticker:
                    return info
            except Exception:
                pass
        return {'name': ticker, 'sector': 'N/A', 'market_cap': None}

    def descargar_datos(self, ticker: str, fecha_inicio: str, fecha_fin: str) -> Tuple[Optional[pd.DataFrame], str]:
        """API compatible con el antiguo data_acquisition.descargar_datos."""
        from datetime import datetime
        try:
            start = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            end   = datetime.strptime(fecha_fin,   '%Y-%m-%d').date()
            df = self.fetch_ohlcv(ticker, start, end)
            info = self.fetch_company_info(ticker)
            df['fecha'] = pd.to_datetime(df['fecha'])
            return df, info.get('name', ticker)
        except AllProvidersFailed as e:
            logger.error(str(e))
            return None, None
        except Exception as e:
            logger.error(f"Error inesperado descargando {ticker}: {e}")
            return None, None


# Instancia global
orchestrator = DataOrchestrator()

# Alias para compatibilidad con código antiguo
def descargar_datos(ticker: str, fecha_inicio: str, fecha_fin: str):
    return orchestrator.descargar_datos(ticker, fecha_inicio, fecha_fin)
