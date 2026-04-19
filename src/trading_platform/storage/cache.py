"""Caché de datos OHLCV en ficheros JSON."""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from trading_platform.core.constants import CACHE_DIR
from trading_platform.core.logging import get_logger

logger = get_logger(__name__)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class CacheManager:
    def __init__(self, expiration_hours: int = 24):
        self.cache_dir = CACHE_DIR
        self.expiration_hours = expiration_hours

    def _key(self, ticker: str, start: str, end: str) -> str:
        return hashlib.md5(f"{ticker}_{start}_{end}".encode()).hexdigest()

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def _expired(self, path: Path) -> bool:
        if not path.exists():
            return True
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return mtime < datetime.now() - timedelta(hours=self.expiration_hours)

    def get(self, ticker: str, start: str, end: str) -> Optional[Tuple[pd.DataFrame, str]]:
        path = self._path(self._key(ticker, start, end))
        if self._expired(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data['data'])
            df['fecha'] = pd.to_datetime(df['fecha'])
            logger.info(f"Cache hit: {ticker}")
            return df, data['company_name']
        except Exception as e:
            logger.warning(f"Cache corrupto para {ticker}: {e}")
            path.unlink(missing_ok=True)
            return None

    def set(self, ticker: str, start: str, end: str, datos: pd.DataFrame, company_name: str):
        path = self._path(self._key(ticker, start, end))
        try:
            df = datos.copy()
            df['fecha'] = df['fecha'].astype(str)
            payload = {
                'ticker': ticker, 'company_name': company_name,
                'cached_at': datetime.now().isoformat(),
                'data': df.to_dict('records')
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f)
            logger.info(f"Cache guardado: {ticker}")
        except Exception as e:
            logger.error(f"Error guardando cache {ticker}: {e}")

    def clear(self, ticker: str = None):
        if ticker:
            for p in self.cache_dir.glob("*.json"):
                try:
                    with open(p) as f:
                        if json.load(f).get('ticker') == ticker:
                            p.unlink()
                except Exception:
                    pass
        else:
            for p in self.cache_dir.glob("*.json"):
                p.unlink(missing_ok=True)

    def stats(self) -> dict:
        files = list(self.cache_dir.glob("*.json"))
        total = len(files)
        expired = sum(1 for f in files if self._expired(f))
        size_mb = sum(f.stat().st_size for f in files) / 1_048_576
        return {'total': total, 'valid': total - expired, 'expired': expired, 'size_mb': round(size_mb, 2)}


cache_manager = CacheManager()
