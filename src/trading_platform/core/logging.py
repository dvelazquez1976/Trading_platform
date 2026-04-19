"""Sistema centralizado de logging."""

import logging
import sys
from pathlib import Path
from typing import Optional


class TradingLogger:
    """Logger singleton para la plataforma."""

    _instance: Optional['TradingLogger'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not TradingLogger._initialized:
            self._setup_logging()
            TradingLogger._initialized = True

    def _setup_logging(self):
        from trading_platform.core.constants import LOG_DIR
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / "control.txt"

        self.logger = logging.getLogger('trading_platform')
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        file_fmt = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_fmt = logging.Formatter('%(levelname)s: %(message)s')

        fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(file_fmt)
        self.logger.addHandler(fh)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(console_fmt)
        self.logger.addHandler(ch)

    def get_logger(self, name: str = None) -> logging.Logger:
        if name:
            return logging.getLogger(f'trading_platform.{name}')
        return self.logger


def get_logger(name: str = None) -> logging.Logger:
    return TradingLogger().get_logger(name)


_trading_logger = TradingLogger()
