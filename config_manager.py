import json
import os
from typing import Dict, Any

class ConfigManager:
    """Gestor de configuración para la plataforma de trading."""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo JSON."""
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(f"Archivo de configuración no encontrado: {self.config_file}")

            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            print(f"Configuración cargada desde {self.config_file}")
            return config

        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear el archivo de configuración: {e}")
        except Exception as e:
            raise RuntimeError(f"Error al cargar configuración: {e}")

    def get(self, section: str, key: str = None, default=None):
        """
        Obtiene un valor de configuración.

        Args:
            section: Sección de la configuración
            key: Clave específica (opcional)
            default: Valor por defecto si no se encuentra
        """
        try:
            if section not in self.config:
                if default is not None:
                    return default
                raise KeyError(f"Sección '{section}' no encontrada en configuración")

            if key is None:
                return self.config[section]

            if key not in self.config[section]:
                if default is not None:
                    return default
                raise KeyError(f"Clave '{key}' no encontrada en sección '{section}'")

            return self.config[section][key]

        except Exception as e:
            print(f"Error al obtener configuración {section}.{key}: {e}")
            return default

    def update(self, section: str, key: str, value: Any):
        """Actualiza un valor de configuración."""
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value

    def save(self):
        """Guarda la configuración actual al archivo."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"Configuración guardada en {self.config_file}")
        except Exception as e:
            raise RuntimeError(f"Error al guardar configuración: {e}")

    def get_indicator_params(self) -> Dict[str, Any]:
        """Obtiene todos los parámetros de indicadores."""
        return self.get('indicators', default={})

    def get_signal_thresholds(self) -> Dict[str, Any]:
        """Obtiene todos los umbrales de señales."""
        return self.get('signals', default={})

    def get_data_config(self) -> Dict[str, Any]:
        """Obtiene configuración de datos."""
        return self.get('data', default={})

    def get_paths_config(self) -> Dict[str, Any]:
        """Obtiene configuración de rutas."""
        return self.get('paths', default={})

# Instancia global del gestor de configuración
config_manager = ConfigManager()