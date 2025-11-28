"""
Gestor de Caché de Datos
=========================

Sistema de caché para datos descargados de Yahoo Finance.
Reduce tiempo de ejecución y llamadas a la API evitando descargas repetidas.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
from logger_config import get_logger

logger = get_logger(__name__)


class CacheManager:
    """
    Gestiona el caché de datos históricos descargados.

    El caché almacena datos en archivos JSON organizados por ticker.
    Incluye validación de expiración y verificación de integridad.
    """

    def __init__(self, cache_dir: str = ".cache", expiration_hours: int = 24):
        """
        Inicializa el gestor de caché.

        Args:
            cache_dir: Directorio para almacenar caché
            expiration_hours: Horas antes de que expire el caché
        """
        self.cache_dir = Path(cache_dir)
        self.expiration_hours = expiration_hours
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"CacheManager inicializado: {self.cache_dir}, expiración {expiration_hours}h")

    def _get_cache_key(self, ticker: str, fecha_inicio: str, fecha_fin: str) -> str:
        """
        Genera clave única para identificar datos en caché.

        Args:
            ticker: Símbolo del ticker
            fecha_inicio: Fecha inicio
            fecha_fin: Fecha fin

        Returns:
            Hash MD5 único
        """
        key_str = f"{ticker}_{fecha_inicio}_{fecha_fin}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_filepath(self, cache_key: str) -> Path:
        """
        Obtiene ruta del archivo de caché.

        Args:
            cache_key: Clave de caché

        Returns:
            Path al archivo de caché
        """
        return self.cache_dir / f"{cache_key}.json"

    def _is_expired(self, filepath: Path) -> bool:
        """
        Verifica si el archivo de caché ha expirado.

        Args:
            filepath: Ruta del archivo

        Returns:
            True si expiró, False si aún válido
        """
        if not filepath.exists():
            return True

        file_time = datetime.fromtimestamp(filepath.stat().st_mtime)
        expiration_time = datetime.now() - timedelta(hours=self.expiration_hours)

        expired = file_time < expiration_time

        if expired:
            logger.debug(f"Caché expirado: {filepath.name}")

        return expired

    def get(self, ticker: str, fecha_inicio: str, fecha_fin: str) -> Optional[Tuple[pd.DataFrame, str]]:
        """
        Obtiene datos del caché si existen y son válidos.

        Args:
            ticker: Símbolo del ticker
            fecha_inicio: Fecha inicio
            fecha_fin: Fecha fin

        Returns:
            Tuple (DataFrame, nombre_empresa) si existe en caché, None si no
        """
        cache_key = self._get_cache_key(ticker, fecha_inicio, fecha_fin)
        filepath = self._get_cache_filepath(cache_key)

        if self._is_expired(filepath):
            logger.debug(f"Cache miss para {ticker} (expirado o no existe)")
            return None

        try:
            logger.debug(f"Leyendo caché para {ticker}")

            with open(filepath, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Reconstruir DataFrame
            df = pd.DataFrame(cache_data['data'])
            df['fecha'] = pd.to_datetime(df['fecha'])

            company_name = cache_data['company_name']

            logger.info(f"Cache hit para {ticker}: {len(df)} registros")
            return df, company_name

        except Exception as e:
            logger.warning(f"Error leyendo caché para {ticker}: {e}")
            # Si hay error, eliminar caché corrupto
            try:
                filepath.unlink()
            except:
                pass
            return None

    def set(self, ticker: str, fecha_inicio: str, fecha_fin: str,
            datos: pd.DataFrame, company_name: str):
        """
        Guarda datos en caché.

        Args:
            ticker: Símbolo del ticker
            fecha_inicio: Fecha inicio
            fecha_fin: Fecha fin
            datos: DataFrame con datos
            company_name: Nombre de la empresa
        """
        cache_key = self._get_cache_key(ticker, fecha_inicio, fecha_fin)
        filepath = self._get_cache_filepath(cache_key)

        try:
            logger.debug(f"Guardando {len(datos)} registros en caché para {ticker}")

            # Preparar datos para JSON
            datos_copy = datos.copy()
            datos_copy['fecha'] = datos_copy['fecha'].astype(str)

            cache_data = {
                'ticker': ticker,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'company_name': company_name,
                'cached_at': datetime.now().isoformat(),
                'data': datos_copy.to_dict('records')
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)

            logger.info(f"Datos guardados en caché para {ticker}")

        except Exception as e:
            logger.error(f"Error guardando caché para {ticker}: {e}")

    def clear(self, ticker: Optional[str] = None):
        """
        Limpia el caché.

        Args:
            ticker: Si se especifica, solo limpia ese ticker. Si None, limpia todo.
        """
        if ticker:
            logger.info(f"Limpiando caché para {ticker}")
            # Buscar y eliminar archivos de ese ticker
            count = 0
            for filepath in self.cache_dir.glob("*.json"):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        if data.get('ticker') == ticker:
                            filepath.unlink()
                            count += 1
                except:
                    pass
            logger.info(f"Eliminados {count} archivos de caché para {ticker}")
        else:
            logger.info("Limpiando todo el caché")
            count = 0
            for filepath in self.cache_dir.glob("*.json"):
                try:
                    filepath.unlink()
                    count += 1
                except:
                    pass
            logger.info(f"Eliminados {count} archivos de caché")

    def clear_expired(self):
        """Elimina archivos de caché expirados."""
        logger.info("Limpiando caché expirado")
        count = 0

        for filepath in self.cache_dir.glob("*.json"):
            if self._is_expired(filepath):
                try:
                    filepath.unlink()
                    count += 1
                except Exception as e:
                    logger.warning(f"Error eliminando caché expirado {filepath}: {e}")

        logger.info(f"Eliminados {count} archivos de caché expirados")

    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del caché.

        Returns:
            Diccionario con estadísticas
        """
        total_files = len(list(self.cache_dir.glob("*.json")))
        expired_files = sum(1 for f in self.cache_dir.glob("*.json") if self._is_expired(f))
        valid_files = total_files - expired_files

        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        size_mb = total_size / (1024 * 1024)

        stats = {
            'total_files': total_files,
            'valid_files': valid_files,
            'expired_files': expired_files,
            'total_size_mb': round(size_mb, 2),
            'cache_dir': str(self.cache_dir)
        }

        logger.debug(f"Estadísticas de caché: {stats}")
        return stats


# Instancia global
_cache_manager = None


def get_cache_manager(cache_dir: str = ".cache", expiration_hours: int = 24) -> CacheManager:
    """
    Obtiene instancia global del gestor de caché.

    Args:
        cache_dir: Directorio de caché
        expiration_hours: Horas de expiración

    Returns:
        Instancia de CacheManager
    """
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = CacheManager(cache_dir, expiration_hours)

    return _cache_manager
