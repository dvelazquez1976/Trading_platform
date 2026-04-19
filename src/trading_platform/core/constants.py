"""Constantes globales de la plataforma de trading."""

from pathlib import Path

# Raíz del proyecto (4 niveles arriba desde este fichero)
ROOT_DIR = Path(__file__).parent.parent.parent.parent

# Rutas estándar
CONFIG_FILE   = ROOT_DIR / "config" / "config.json"
DATA_DIR      = ROOT_DIR / "data"
MARKETS_DIR   = DATA_DIR / "markets"
WATCHLISTS_DIR = DATA_DIR / "watchlists"
CACHE_DIR     = DATA_DIR / "cache"
DB_DIR        = DATA_DIR / "db"
OUTPUTS_DIR   = DATA_DIR / "outputs"
LOG_DIR       = OUTPUTS_DIR / "logs"
REPORTS_DIR   = OUTPUTS_DIR / "reports"
CSV_DIR       = OUTPUTS_DIR / "csv"

# Columnas OHLCV
STANDARD_COLUMNS = {
    'SPANISH': ['fecha', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen'],
    'ENGLISH': ['date', 'open', 'high', 'low', 'close', 'volume']
}

COLUMN_MAPPING_ES_EN = {
    'fecha': 'date', 'apertura': 'open', 'maximo': 'high',
    'minimo': 'low',  'cierre': 'close', 'volumen': 'volume'
}
COLUMN_MAPPING_EN_ES = {v: k for k, v in COLUMN_MAPPING_ES_EN.items()}

YFINANCE_COLUMN_MAPPING = {
    "Date": "fecha", "Open": "apertura", "High": "maximo",
    "Low": "minimo", "Close": "cierre", "Volume": "volumen"
}

# CSV export
CSV_DATA_TYPES = {
    'apertura': 'open', 'maximo': 'high', 'minimo': 'low',
    'cierre': 'close', 'volumen': 'volume'
}

# Indicadores
AVAILABLE_INDICATORS = [
    "Cruce_Medias", "RSI", "Estocastico", "MACD",
    "Bandas_Bollinger", "Williams_R", "Awesome_Oscillator", "ROC"
]
ADVANCED_INDICATORS = [
    "Stochastic_RSI", "TSI", "Ultimate_Oscillator", "Chaikin_Oscillator",
    "Aroon_Oscillator", "TRIX", "Volume_RSI", "DPO"
]
INDICATOR_RESULT_COLUMNS = [
    "SMA_30", "RSI", "STOCHk", "MACD",
    "BBM_BB", "CCI", "ADX", "MFI", "WILLR", "AO", "ROC"
]
ADVANCED_INDICATOR_COLUMNS = [
    "STOCHRSI_K", "TSI", "UO", "CHAIKIN_OSC",
    "AROONOSC", "TRIX", "VOLRSI", "DPO"
]
BASE_TABLE_HEADERS = ["Ticker", "Empresa", "Fecha", "Precio Cierre", "Recomendación"]
TABLE_HEADERS = BASE_TABLE_HEADERS + AVAILABLE_INDICATORS + INDICATOR_RESULT_COLUMNS

# Señales
SIGNAL_TYPES = {
    'BUY': 'COMPRA', 'SELL': 'VENTA',
    'HOLD': 'KEEP/NO SIGNAL', 'NEUTRAL': 'KEEP'
}

# Configuración por defecto
DEFAULT_CONFIG = {
    'indicators': {
        'sma_periods': [30, 60, 90], 'rsi_period': 14,
        'stoch_params': {"k": 14, "d": 3},
        'macd_params': {"fast": 12, "slow": 26, "signal": 9},
        'bollinger_params': {"length": 20, "std": 2},
        'cci_period': 20, 'adx_period': 14, 'mfi_period': 14,
        'willr_period': 14, 'ao_params': {"fast": 5, "slow": 34}, 'roc_period': 12
    },
    'signals': {
        'rsi_oversold': 30, 'rsi_overbought': 70,
        'stoch_oversold': 20, 'stoch_overbought': 80,
        'willr_oversold': -80, 'willr_overbought': -20,
        'roc_bullish': 5, 'roc_bearish': -5
    }
}
