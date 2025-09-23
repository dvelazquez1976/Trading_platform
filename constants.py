"""Constantes utilizadas en la plataforma de trading."""

# Columnas de datos estándar
STANDARD_COLUMNS = {
    'SPANISH': ['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen'],
    'ENGLISH': ['date', 'open', 'high', 'low', 'close', 'volume']
}

# Mapeo de columnas español-inglés
COLUMN_MAPPING_ES_EN = {
    'fecha': 'date',
    'apertura': 'open',
    'maximo': 'high',
    'minimo': 'low',
    'cierre': 'close',
    'volumen': 'volume'
}

# Mapeo de columnas inglés-español
COLUMN_MAPPING_EN_ES = {v: k for k, v in COLUMN_MAPPING_ES_EN.items()}

# Mapeo específico para Yahoo Finance
YFINANCE_COLUMN_MAPPING = {
    "Date": "fecha",
    "Open": "apertura",
    "High": "maximo",
    "Low": "minimo",
    "Close": "cierre",
    "Volume": "volumen"
}

# Tipos de datos para CSV export
CSV_DATA_TYPES = {
    'apertura': 'open',
    'maximo': 'high',
    'minimo': 'low',
    'cierre': 'close',
    'volumen': 'volume'
}

# Indicadores disponibles en el sistema
AVAILABLE_INDICATORS = [
    "Cruce_Medias", "RSI", "Estocastico", "MACD",
    "Bandas_Bollinger", "Williams_R", "Awesome_Oscillator", "ROC"
]

# Indicadores avanzados disponibles
ADVANCED_INDICATORS = [
    "Stochastic_RSI", "TSI", "Ultimate_Oscillator", "Chaikin_Oscillator",
    "Aroon_Oscillator", "TRIX", "Volume_RSI", "DPO"
]

# Columnas de indicadores en la tabla de resultados
INDICATOR_RESULT_COLUMNS = [
    "SMA_30", "RSI_14", "STOCHk_14_3_3", "MACD_12_26_9",
    "BBM_20_2", "CCI_20", "ADX_14", "MFI_14",
    "WILLR_14", "AO_5_34", "ROC_12"
]

# Columnas de indicadores avanzados
ADVANCED_INDICATOR_COLUMNS = [
    "STOCHRSI_K", "TSI", "UO", "CHAIKIN_OSC",
    "AROONOSC", "TRIX", "VOLRSI", "DPO"
]

# Headers para la tabla de resultados (se actualizará dinámicamente)
BASE_TABLE_HEADERS = [
    "Ticker", "Empresa", "Fecha", "Precio Cierre", "Recomendación"
]

# Headers completos (se construirán dinámicamente)
TABLE_HEADERS = BASE_TABLE_HEADERS + AVAILABLE_INDICATORS + INDICATOR_RESULT_COLUMNS

# Tipos de señales
SIGNAL_TYPES = {
    'BUY': 'COMPRA',
    'SELL': 'VENTA',
    'HOLD': 'KEEP/NO SIGNAL',
    'NEUTRAL': 'KEEP'
}

# Valores por defecto para configuración
DEFAULT_CONFIG = {
    'indicators': {
        'sma_periods': [30, 60, 90],
        'rsi_period': 14,
        'stoch_params': {"k": 14, "d": 3},
        'macd_params': {"fast": 12, "slow": 26, "signal": 9},
        'bollinger_params': {"length": 20, "std": 2},
        'cci_period': 20,
        'adx_period': 14,
        'mfi_period': 14,
        'willr_period': 14,
        'ao_params': {"fast": 5, "slow": 34},
        'roc_period': 12
    },
    'signals': {
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'stoch_oversold': 20,
        'stoch_overbought': 80,
        'willr_oversold': -80,
        'willr_overbought': -20,
        'roc_bullish': 5,
        'roc_bearish': -5
    }
}

# Paths por defecto
DEFAULT_PATHS = {
    'database_file': 'plataforma_trading.db',
    'tickers_file': 'tickers.txt',
    'output_file': 'Salida.txt',
    'output_directory': 'salidas',
    'config_file': 'config.json'
}