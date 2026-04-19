"""Interfaz abstracta DataProvider — todo proveedor debe cumplir este contrato."""

from datetime import date
from typing import Optional, Tuple
import pandas as pd


class DataProvider:
    """Clase base para proveedores de datos financieros."""

    name: str = "base"
    is_free: bool = True
    requires_api_key: bool = False

    # Sufijos de mercado que este proveedor soporta (vacío = todos)
    supported_suffixes: tuple = ()

    def fetch_ohlcv(self, ticker: str, start: date, end: date) -> Optional[pd.DataFrame]:
        """Retorna DataFrame con columnas [fecha, apertura, maximo, minimo, cierre, volumen]."""
        raise NotImplementedError

    def fetch_company_info(self, ticker: str) -> dict:
        """Retorna dict con al menos 'name', 'sector', 'market_cap'."""
        raise NotImplementedError

    def supports(self, ticker: str) -> bool:
        """True si este proveedor puede manejar el ticker dado."""
        if not self.supported_suffixes:
            return True
        ticker_upper = ticker.upper()
        return any(ticker_upper.endswith(s) for s in self.supported_suffixes)

    def __repr__(self):
        return f"<{self.__class__.__name__} free={self.is_free}>"


class ProviderError(Exception):
    """Error al obtener datos de un proveedor."""
    pass


class AllProvidersFailed(Exception):
    """Todos los proveedores fallaron para un ticker."""
    pass
