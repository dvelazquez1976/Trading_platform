"""Gestión de watchlists persistentes en data/watchlists/."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from trading_platform.core.constants import WATCHLISTS_DIR
from trading_platform.core.logging import get_logger

logger = get_logger(__name__)

_SAFE_NAME = re.compile(r"[^\w\-]")
_COLUMNS = ["ticker", "name", "sector"]


def _slug(name: str) -> str:
    """Convierte nombre libre en nombre de fichero seguro."""
    return _SAFE_NAME.sub("_", name.strip().lower())[:50] or "watchlist"


def list_watchlists() -> list[dict]:
    """Devuelve metadatos de todas las watchlists guardadas, ordenadas por fecha."""
    WATCHLISTS_DIR.mkdir(parents=True, exist_ok=True)
    result = []
    for p in sorted(WATCHLISTS_DIR.glob("*.csv"), key=lambda f: f.stat().st_mtime, reverse=True):
        try:
            df = pd.read_csv(p)
            result.append({
                "filename": p.name,
                "display_name": p.stem.replace("_", " ").title(),
                "tickers": len(df),
                "modified": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                "path": p,
            })
        except Exception:
            pass
    return result


def load_watchlist(filename: str) -> Optional[list[dict]]:
    """Carga una watchlist por nombre de fichero. Devuelve lista de dicts."""
    path = WATCHLISTS_DIR / filename
    if not path.exists():
        logger.warning(f"Watchlist no encontrada: {filename}")
        return None
    try:
        df = pd.read_csv(path)
        for col in _COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[_COLUMNS].to_dict("records")
    except Exception as e:
        logger.error(f"Error cargando watchlist {filename}: {e}")
        return None


def save_watchlist(records: list[dict], name: str) -> Path:
    """Guarda la watchlist con el nombre dado. Devuelve la ruta del fichero."""
    WATCHLISTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{_slug(name)}.csv"
    path = WATCHLISTS_DIR / filename
    df = pd.DataFrame(records)
    for col in _COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df[_COLUMNS].to_csv(path, index=False)
    logger.info(f"Watchlist guardada: {path}")
    return path


def delete_watchlist(filename: str) -> bool:
    """Elimina una watchlist. Devuelve True si se borró."""
    path = WATCHLISTS_DIR / filename
    if path.exists():
        path.unlink()
        logger.info(f"Watchlist eliminada: {filename}")
        return True
    return False


def rename_watchlist(old_filename: str, new_name: str) -> Optional[Path]:
    """Renombra una watchlist. Devuelve la nueva ruta o None si falla."""
    old_path = WATCHLISTS_DIR / old_filename
    if not old_path.exists():
        return None
    new_path = WATCHLISTS_DIR / f"{_slug(new_name)}.csv"
    old_path.rename(new_path)
    return new_path
