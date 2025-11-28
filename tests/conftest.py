"""
Configuración compartida de pytest y fixtures comunes.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import os
import tempfile


@pytest.fixture
def sample_ticker():
    """Fixture que proporciona un ticker de prueba."""
    return "AAPL"


@pytest.fixture
def date_range():
    """Fixture que proporciona un rango de fechas para pruebas."""
    fecha_fin = datetime.now().date()
    fecha_inicio = fecha_fin - timedelta(days=90)
    return fecha_inicio.strftime("%Y-%m-%d"), fecha_fin.strftime("%Y-%m-%d")


@pytest.fixture
def sample_historical_data():
    """
    Fixture que crea un DataFrame de ejemplo con datos históricos.
    """
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # Generar datos de precio simulados
    base_price = 150.0
    prices = [base_price + i * 0.5 for i in range(100)]

    data = {
        'fecha': dates,
        'apertura': [p - 1 for p in prices],
        'maximo': [p + 2 for p in prices],
        'minimo': [p - 2 for p in prices],
        'cierre': prices,
        'volumen': [1000000 + i * 10000 for i in range(100)]
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_data_with_indicators(sample_historical_data):
    """
    Fixture que crea un DataFrame con datos e indicadores calculados.
    """
    df = sample_historical_data.copy()

    # Agregar algunos indicadores básicos simulados
    df['SMA_30'] = df['cierre'].rolling(window=30, min_periods=1).mean()
    df['SMA_60'] = df['cierre'].rolling(window=60, min_periods=1).mean()
    df['RSI'] = 50.0  # RSI neutral
    df['STOCHk_14_3_3'] = 50.0
    df['STOCHd_14_3_3'] = 50.0
    df['MACD_12_26_9'] = 0.0
    df['MACDs_12_26_9'] = 0.0
    df['BBL_20_2.0_2.0'] = df['cierre'] - 10
    df['BBU_20_2.0_2.0'] = df['cierre'] + 10
    df['WILLR'] = -50.0
    df['AO'] = 0.0
    df['ROC'] = 0.0
    df['ticker'] = 'AAPL'

    return df


@pytest.fixture
def temp_db_path():
    """Fixture que proporciona una ruta temporal para base de datos de pruebas."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def temp_cache_dir():
    """Fixture que proporciona un directorio temporal para caché de pruebas."""
    temp_dir = tempfile.mkdtemp()

    yield temp_dir

    # Cleanup
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_signal_result():
    """Fixture que proporciona un resultado de señales de ejemplo."""
    return {
        'ticker': 'AAPL',
        'fecha': '2024-01-15',
        'precio_cierre': 150.0,
        'señales': {
            'Cruce_Medias': 'KEEP/NO SIGNAL',
            'RSI': 'KEEP/NO SIGNAL',
            'Estocastico': 'KEEP/NO SIGNAL',
            'MACD': 'KEEP/NO SIGNAL',
            'Bandas_Bollinger': 'KEEP/NO SIGNAL',
            'Williams_R': 'KEEP/NO SIGNAL',
            'Awesome_Oscillator': 'KEEP/NO SIGNAL',
            'ROC': 'KEEP/NO SIGNAL'
        },
        'resumen': 'KEEP'
    }


@pytest.fixture(autouse=True)
def reset_config():
    """Fixture que resetea la configuración antes de cada test."""
    from config_manager import config_manager
    # No necesitamos hacer nada especial aquí por ahora
    yield
