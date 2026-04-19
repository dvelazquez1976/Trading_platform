"""Gestor de configuración — lee config/config.json relativo a la raíz del proyecto."""

import json
from pathlib import Path
from typing import Any, Dict

from trading_platform.core.constants import CONFIG_FILE, DEFAULT_CONFIG


class ConfigManager:
    """Carga y expone config/config.json con fallback a DEFAULT_CONFIG."""

    def __init__(self, config_file: Path = CONFIG_FILE):
        self.config_file = config_file
        self.config = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.config_file.exists():
            print(f"[config] {self.config_file} no encontrado — usando defaults")
            return DEFAULT_CONFIG.copy()
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parseando config: {e}")

    def get(self, section: str, key: str = None, default=None):
        try:
            section_data = self.config.get(section, default)
            if section_data is None:
                return default
            if key is None:
                return section_data
            return section_data.get(key, default)
        except Exception:
            return default

    def set(self, section: str, key: str, value: Any):
        self.config.setdefault(section, {})[key] = value

    def save(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def reload(self):
        self.config = self._load()

    # Helpers
    def get_indicator_params(self) -> Dict[str, Any]:
        return self.get('indicators', default={})

    def get_signal_thresholds(self) -> Dict[str, Any]:
        return self.get('signals', default={})

    def get_data_config(self) -> Dict[str, Any]:
        return self.get('data', default={})


config_manager = ConfigManager()
