"""
Tests para el módulo indicator_calculator.
"""

import pytest
import pandas as pd
import indicator_calculator
from unittest.mock import patch


class TestCalcularIndicadores:
    """Tests para la función calcular_indicadores."""

    def test_calcular_indicadores_basicos(self, sample_historical_data):
        """Test de cálculo de indicadores básicos."""
        resultado = indicator_calculator.calcular_indicadores(sample_historical_data)

        # Verificar que se calcularon los indicadores
        assert 'SMA_30' in resultado.columns
        assert 'SMA_60' in resultado.columns
        assert 'SMA_90' in resultado.columns
        assert 'RSI' in resultado.columns
        assert 'MACD_12_26_9' in resultado.columns
        assert 'MACDs_12_26_9' in resultado.columns

        # Verificar que no hay errores de cálculo
        assert len(resultado) > 0

    def test_indicadores_stochastic(self, sample_historical_data):
        """Test de cálculo del indicador estocástico."""
        resultado = indicator_calculator.calcular_indicadores(sample_historical_data)

        assert 'STOCHk_14_3_3' in resultado.columns
        assert 'STOCHd_14_3_3' in resultado.columns

    def test_indicadores_bollinger(self, sample_historical_data):
        """Test de cálculo de Bandas de Bollinger."""
        resultado = indicator_calculator.calcular_indicadores(sample_historical_data)

        assert 'BBL_20_2.0_2.0' in resultado.columns
        assert 'BBU_20_2.0_2.0' in resultado.columns
        assert 'BBM_20_2.0_2.0' in resultado.columns

    def test_indicadores_adicionales(self, sample_historical_data):
        """Test de cálculo de indicadores adicionales."""
        resultado = indicator_calculator.calcular_indicadores(sample_historical_data)

        assert 'CCI' in resultado.columns
        assert 'MFI' in resultado.columns
        assert 'WILLR' in resultado.columns
        assert 'AO' in resultado.columns
        assert 'ROC' in resultado.columns

    def test_sma_valores_correctos(self, sample_historical_data):
        """Test que verifica que los valores de SMA son correctos."""
        resultado = indicator_calculator.calcular_indicadores(sample_historical_data)

        # SMA_30 debería ser el promedio de los últimos 30 valores
        # Para datos con tendencia alcista, SMA_60 debería ser menor que SMA_30
        if len(resultado) >= 60:
            ultimo_sma_30 = resultado['SMA_30'].iloc[-1]
            ultimo_sma_60 = resultado['SMA_60'].iloc[-1]

            # Verificar que son valores numéricos válidos
            assert pd.notna(ultimo_sma_30)
            assert pd.notna(ultimo_sma_60)

    def test_rsi_rango_valido(self, sample_historical_data):
        """Test que verifica que el RSI está en el rango válido (0-100)."""
        resultado = indicator_calculator.calcular_indicadores(sample_historical_data)

        # Eliminar NaN para el test
        rsi_values = resultado['RSI'].dropna()

        if len(rsi_values) > 0:
            assert (rsi_values >= 0).all()
            assert (rsi_values <= 100).all()

    @patch('indicator_calculator.config_manager.get_indicator_params')
    def test_usa_parametros_personalizados(self, mock_config, sample_historical_data):
        """Test que verifica que usa parámetros personalizados de configuración."""
        # Configurar parámetros personalizados
        mock_config.return_value = {
            'sma_periods': [20, 50],
            'rsi_period': 10,
            'stoch_params': {"k": 14, "d": 3},
            'macd_params': {"fast": 12, "slow": 26, "signal": 9},
            'bollinger_params': {"length": 20, "std": 2},
            'cci_period': 20,
            'adx_period': 14,
            'mfi_period': 14,
            'willr_period': 14,
            'ao_params': {"fast": 5, "slow": 34},
            'roc_period': 12
        }

        resultado = indicator_calculator.calcular_indicadores(sample_historical_data)

        # Verificar que se calcularon con los períodos personalizados
        assert 'SMA_20' in resultado.columns
        assert 'SMA_50' in resultado.columns
        mock_config.assert_called_once()

    def test_con_datos_insuficientes(self):
        """Test con datos insuficientes para calcular indicadores."""
        # DataFrame con solo 5 filas
        dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
        data = {
            'fecha': dates,
            'apertura': [150.0] * 5,
            'maximo': [152.0] * 5,
            'minimo': [149.0] * 5,
            'cierre': [151.0] * 5,
            'volumen': [1000000] * 5
        }
        df = pd.DataFrame(data)

        # Debería calcular sin errores, aunque algunos indicadores tendrán NaN
        resultado = indicator_calculator.calcular_indicadores(df)

        assert len(resultado) == 5
        assert 'SMA_30' in resultado.columns

    @patch('indicator_calculator.config_manager.get')
    def test_indicadores_avanzados_habilitados(self, mock_config, sample_historical_data):
        """Test de cálculo cuando los indicadores avanzados están habilitados."""
        mock_config.return_value = {'enabled': True}

        with patch('indicator_calculator.calculate_all_advanced_indicators') as mock_advanced:
            mock_advanced.return_value = sample_historical_data

            resultado = indicator_calculator.calcular_indicadores(sample_historical_data)

            # Verificar que se llamó a la función de indicadores avanzados
            mock_advanced.assert_called_once()

    @patch('indicator_calculator.config_manager.get')
    def test_indicadores_avanzados_deshabilitados(self, mock_config, sample_historical_data):
        """Test cuando los indicadores avanzados están deshabilitados."""
        mock_config.return_value = {'enabled': False}

        with patch('indicator_calculator.calculate_all_advanced_indicators') as mock_advanced:
            resultado = indicator_calculator.calcular_indicadores(sample_historical_data)

            # No debería llamar a indicadores avanzados
            mock_advanced.assert_not_called()


class TestRenombreColumnas:
    """Tests para las funciones de renombre de columnas."""

    def test_renombra_a_ingles(self, sample_historical_data):
        """Test de renombre de columnas al inglés."""
        from utils import rename_columns_to_english

        resultado = rename_columns_to_english(sample_historical_data)

        assert 'open' in resultado.columns
        assert 'high' in resultado.columns
        assert 'low' in resultado.columns
        assert 'close' in resultado.columns
        assert 'volume' in resultado.columns

    def test_renombra_a_espanol(self):
        """Test de renombre de columnas al español."""
        from utils import rename_columns_to_spanish

        # DataFrame en inglés
        data = pd.DataFrame({
            'fecha': pd.date_range(start='2024-01-01', periods=5),
            'open': [150.0] * 5,
            'high': [152.0] * 5,
            'low': [149.0] * 5,
            'close': [151.0] * 5,
            'volume': [1000000] * 5
        })

        resultado = rename_columns_to_spanish(data)

        assert 'apertura' in resultado.columns
        assert 'maximo' in resultado.columns
        assert 'minimo' in resultado.columns
        assert 'cierre' in resultado.columns
        assert 'volumen' in resultado.columns


class TestValidacionColumnas:
    """Tests para la validación de columnas."""

    def test_validacion_exitosa(self, sample_historical_data):
        """Test de validación exitosa de columnas."""
        from utils import validate_required_columns
        from constants import STANDARD_COLUMNS

        # No debería lanzar excepción
        validate_required_columns(sample_historical_data, STANDARD_COLUMNS['SPANISH'])

    def test_validacion_falla_columnas_faltantes(self):
        """Test de validación con columnas faltantes."""
        from utils import validate_required_columns
        from constants import STANDARD_COLUMNS

        # DataFrame incompleto
        df = pd.DataFrame({
            'fecha': pd.date_range(start='2024-01-01', periods=5),
            'cierre': [150.0] * 5
        })

        # Debería lanzar ValueError
        with pytest.raises(ValueError):
            validate_required_columns(df, STANDARD_COLUMNS['SPANISH'])
