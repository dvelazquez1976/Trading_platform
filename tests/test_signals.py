"""
Tests para el módulo signal_generator.
"""

import pytest
import pandas as pd
import signal_generator
from unittest.mock import patch


class TestGenerarSenales:
    """Tests para la función generar_senales."""

    def test_generar_senales_basicas(self, sample_data_with_indicators):
        """Test de generación de señales básicas."""
        resultado = signal_generator.generar_senales(sample_data_with_indicators)

        # Verificar estructura del resultado
        assert 'ticker' in resultado
        assert 'fecha' in resultado
        assert 'precio_cierre' in resultado
        assert 'señales' in resultado
        assert 'resumen' in resultado

        # Verificar señales básicas
        senales = resultado['señales']
        assert 'Cruce_Medias' in senales
        assert 'RSI' in senales
        assert 'Estocastico' in senales
        assert 'MACD' in senales
        assert 'Bandas_Bollinger' in senales
        assert 'Williams_R' in senales
        assert 'Awesome_Oscillator' in senales
        assert 'ROC' in senales

    def test_senales_valores_validos(self, sample_data_with_indicators):
        """Test que verifica que las señales tienen valores válidos."""
        resultado = signal_generator.generar_senales(sample_data_with_indicators)

        valores_validos = {
            signal_generator.SIGNAL_BUY,
            signal_generator.SIGNAL_SELL,
            signal_generator.SIGNAL_HOLD
        }

        for senal in resultado['señales'].values():
            assert senal in valores_validos

    def test_resumen_valores_validos(self, sample_data_with_indicators):
        """Test que el resumen tiene valores válidos."""
        resultado = signal_generator.generar_senales(sample_data_with_indicators)

        assert resultado['resumen'] in ['COMPRA', 'VENTA', 'KEEP']

    def test_cruce_medias_alcista(self):
        """Test de señal de compra por cruce de medias alcista."""
        # Crear datos con cruce alcista
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = {
            'fecha': dates,
            'apertura': [150.0] * 100,
            'maximo': [152.0] * 100,
            'minimo': [149.0] * 100,
            'cierre': [151.0] * 100,
            'volumen': [1000000] * 100,
            'ticker': ['AAPL'] * 100
        }
        df = pd.DataFrame(data)

        # Simular cruce alcista: SMA_30 cruza sobre SMA_60
        df['SMA_30'] = 149.0
        df['SMA_60'] = 150.0
        df.loc[df.index[-1], 'SMA_30'] = 151.0  # Último valor cruza hacia arriba
        df.loc[df.index[-1], 'SMA_60'] = 150.0

        # Agregar otros indicadores necesarios
        df['RSI'] = 50.0
        df['STOCHk_14_3_3'] = 50.0
        df['STOCHd_14_3_3'] = 50.0
        df['MACD_12_26_9'] = 0.0
        df['MACDs_12_26_9'] = 0.0
        df['BBL_20_2.0_2.0'] = 145.0
        df['BBU_20_2.0_2.0'] = 155.0
        df['WILLR'] = -50.0
        df['AO'] = 0.0
        df['ROC'] = 0.0

        resultado = signal_generator.generar_senales(df)

        assert resultado['señales']['Cruce_Medias'] == signal_generator.SIGNAL_BUY

    def test_cruce_medias_bajista(self):
        """Test de señal de venta por cruce de medias bajista."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = {
            'fecha': dates,
            'apertura': [150.0] * 100,
            'maximo': [152.0] * 100,
            'minimo': [149.0] * 100,
            'cierre': [151.0] * 100,
            'volumen': [1000000] * 100,
            'ticker': ['AAPL'] * 100
        }
        df = pd.DataFrame(data)

        # Simular cruce bajista
        df['SMA_30'] = 151.0
        df['SMA_60'] = 150.0
        df.loc[df.index[-1], 'SMA_30'] = 149.0  # Cruza hacia abajo
        df.loc[df.index[-1], 'SMA_60'] = 150.0

        # Agregar otros indicadores
        df['RSI'] = 50.0
        df['STOCHk_14_3_3'] = 50.0
        df['STOCHd_14_3_3'] = 50.0
        df['MACD_12_26_9'] = 0.0
        df['MACDs_12_26_9'] = 0.0
        df['BBL_20_2.0_2.0'] = 145.0
        df['BBU_20_2.0_2.0'] = 155.0
        df['WILLR'] = -50.0
        df['AO'] = 0.0
        df['ROC'] = 0.0

        resultado = signal_generator.generar_senales(df)

        assert resultado['señales']['Cruce_Medias'] == signal_generator.SIGNAL_SELL

    def test_rsi_sobreventa(self, sample_data_with_indicators):
        """Test de señal de compra por RSI en sobreventa."""
        df = sample_data_with_indicators.copy()
        df.loc[df.index[-1], 'RSI'] = 25.0  # RSI en sobreventa

        resultado = signal_generator.generar_senales(df)

        assert resultado['señales']['RSI'] == signal_generator.SIGNAL_BUY

    def test_rsi_sobrecompra(self, sample_data_with_indicators):
        """Test de señal de venta por RSI en sobrecompra."""
        df = sample_data_with_indicators.copy()
        df.loc[df.index[-1], 'RSI'] = 75.0  # RSI en sobrecompra

        resultado = signal_generator.generar_senales(df)

        assert resultado['señales']['RSI'] == signal_generator.SIGNAL_SELL

    def test_bandas_bollinger_precio_bajo_banda_inferior(self, sample_data_with_indicators):
        """Test de señal de compra cuando el precio está bajo la banda inferior."""
        df = sample_data_with_indicators.copy()
        precio_cierre = 100.0
        df.loc[df.index[-1], 'cierre'] = precio_cierre
        df.loc[df.index[-1], 'BBL_20_2.0_2.0'] = precio_cierre + 1  # Banda inferior arriba del precio

        resultado = signal_generator.generar_senales(df)

        assert resultado['señales']['Bandas_Bollinger'] == signal_generator.SIGNAL_BUY

    def test_bandas_bollinger_precio_sobre_banda_superior(self, sample_data_with_indicators):
        """Test de señal de venta cuando el precio está sobre la banda superior."""
        df = sample_data_with_indicators.copy()
        precio_cierre = 200.0
        df.loc[df.index[-1], 'cierre'] = precio_cierre
        df.loc[df.index[-1], 'BBU_20_2.0_2.0'] = precio_cierre - 1  # Banda superior debajo del precio

        resultado = signal_generator.generar_senales(df)

        assert resultado['señales']['Bandas_Bollinger'] == signal_generator.SIGNAL_SELL

    @patch('signal_generator.config_manager.get_signal_thresholds')
    def test_usa_umbrales_personalizados(self, mock_thresholds, sample_data_with_indicators):
        """Test que verifica que usa umbrales personalizados."""
        mock_thresholds.return_value = {
            'rsi_oversold': 35,
            'rsi_overbought': 65,
            'stoch_oversold': 25,
            'stoch_overbought': 75,
            'willr_oversold': -75,
            'willr_overbought': -25,
            'roc_bullish': 3,
            'roc_bearish': -3
        }

        df = sample_data_with_indicators.copy()
        df.loc[df.index[-1], 'RSI'] = 34.0  # Justo bajo el umbral personalizado

        resultado = signal_generator.generar_senales(df)

        assert resultado['señales']['RSI'] == signal_generator.SIGNAL_BUY
        mock_thresholds.assert_called()

    def test_resumen_mayoria_compra(self, sample_data_with_indicators):
        """Test que el resumen es COMPRA cuando la mayoría de señales son de compra."""
        df = sample_data_with_indicators.copy()

        # Configurar para generar señales de compra
        df.loc[df.index[-1], 'RSI'] = 25.0  # Sobreventa
        df.loc[df.index[-1], 'WILLR'] = -85.0  # Sobreventa
        df.loc[df.index[-1], 'ROC'] = 10.0  # Alcista

        with patch('signal_generator.generate_advanced_signals', return_value={}):
            resultado = signal_generator.generar_senales(df)

            # Contar señales de compra
            compras = sum(1 for s in resultado['señales'].values() if s == signal_generator.SIGNAL_BUY)
            ventas = sum(1 for s in resultado['señales'].values() if s == signal_generator.SIGNAL_SELL)

            if compras > ventas:
                assert resultado['resumen'] == 'COMPRA'

    def test_resumen_mayoria_venta(self, sample_data_with_indicators):
        """Test que el resumen es VENTA cuando la mayoría de señales son de venta."""
        df = sample_data_with_indicators.copy()

        # Configurar para generar señales de venta
        df.loc[df.index[-1], 'RSI'] = 75.0  # Sobrecompra
        df.loc[df.index[-1], 'WILLR'] = -15.0  # Sobrecompra
        df.loc[df.index[-1], 'ROC'] = -10.0  # Bajista

        with patch('signal_generator.generate_advanced_signals', return_value={}):
            resultado = signal_generator.generar_senales(df)

            compras = sum(1 for s in resultado['señales'].values() if s == signal_generator.SIGNAL_BUY)
            ventas = sum(1 for s in resultado['señales'].values() if s == signal_generator.SIGNAL_SELL)

            if ventas > compras:
                assert resultado['resumen'] == 'VENTA'


class TestFuncionesAuxiliares:
    """Tests para funciones auxiliares del módulo."""

    def test_evaluar_cruce_alcista(self):
        """Test de evaluación de cruce alcista."""
        from signal_generator import _evaluar_cruce

        # Valor cruza hacia arriba
        senal = _evaluar_cruce(
            valor_actual=51.0,
            valor_ref_actual=50.0,
            valor_anterior=49.0,
            valor_ref_anterior=50.0
        )

        assert senal == signal_generator.SIGNAL_BUY

    def test_evaluar_cruce_bajista(self):
        """Test de evaluación de cruce bajista."""
        from signal_generator import _evaluar_cruce

        # Valor cruza hacia abajo
        senal = _evaluar_cruce(
            valor_actual=49.0,
            valor_ref_actual=50.0,
            valor_anterior=51.0,
            valor_ref_anterior=50.0
        )

        assert senal == signal_generator.SIGNAL_SELL

    def test_evaluar_umbral_sobreventa(self):
        """Test de evaluación de umbral en sobreventa."""
        from signal_generator import _evaluar_umbral

        senal = _evaluar_umbral(
            valor=25.0,
            umbral_inferior=30.0,
            umbral_superior=70.0
        )

        assert senal == signal_generator.SIGNAL_BUY

    def test_evaluar_umbral_sobrecompra(self):
        """Test de evaluación de umbral en sobrecompra."""
        from signal_generator import _evaluar_umbral

        senal = _evaluar_umbral(
            valor=75.0,
            umbral_inferior=30.0,
            umbral_superior=70.0
        )

        assert senal == signal_generator.SIGNAL_SELL

    def test_evaluar_umbral_neutral(self):
        """Test de evaluación de umbral en zona neutral."""
        from signal_generator import _evaluar_umbral

        senal = _evaluar_umbral(
            valor=50.0,
            umbral_inferior=30.0,
            umbral_superior=70.0
        )

        assert senal == signal_generator.SIGNAL_HOLD
