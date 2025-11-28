"""Configuración centralizada del sistema de logging."""

import logging
import sys
from pathlib import Path
from typing import Optional


class TradingLogger:
    """
    Gestor centralizado de logging para la plataforma de trading.

    Proporciona logging a archivo y consola con niveles configurables.
    """

    _instance: Optional['TradingLogger'] = None
    _initialized: bool = False

    def __new__(cls):
        """Implementa patrón Singleton para el logger."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializa el sistema de logging si no está ya inicializado."""
        if not TradingLogger._initialized:
            self._setup_logging()
            TradingLogger._initialized = True

    def _setup_logging(self):
        """Configura los handlers y formatos de logging."""
        # Crear logger raíz para la aplicación
        self.logger = logging.getLogger('trading_platform')
        self.logger.setLevel(logging.DEBUG)

        # Evitar duplicación de logs
        self.logger.handlers.clear()

        # Formato detallado para archivos
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Formato simple para consola
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

        # Handler para archivo de control (todos los niveles)
        control_handler = logging.FileHandler('control.txt', mode='w', encoding='utf-8')
        control_handler.setLevel(logging.DEBUG)
        control_handler.setFormatter(file_formatter)
        self.logger.addHandler(control_handler)

        # Handler para consola (solo INFO y superior)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

    def get_logger(self, name: str = None) -> logging.Logger:
        """
        Obtiene un logger con el nombre especificado.

        Args:
            name: Nombre del módulo que solicita el logger

        Returns:
            Logger configurado
        """
        if name:
            return logging.getLogger(f'trading_platform.{name}')
        return self.logger

    def add_file_handler(self, filepath: str, level: int = logging.INFO):
        """
        Añade un handler adicional para escribir en un archivo específico.

        Args:
            filepath: Ruta del archivo de log
            level: Nivel mínimo de logging
        """
        handler = logging.FileHandler(filepath, mode='a', encoding='utf-8')
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)


# Función de conveniencia para obtener logger
def get_logger(name: str = None) -> logging.Logger:
    """
    Función de conveniencia para obtener un logger configurado.

    Args:
        name: Nombre del módulo

    Returns:
        Logger configurado

    Example:
        >>> from logger_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Mensaje informativo")
    """
    trading_logger = TradingLogger()
    return trading_logger.get_logger(name)


# Inicializar el sistema de logging al importar el módulo
_trading_logger = TradingLogger()
