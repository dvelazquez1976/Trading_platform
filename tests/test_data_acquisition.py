"""
Tests para el módulo data_acquisition.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import data_acquisition


class TestDescargarDatos:
    """Tests para la función descargar_datos."""

    @patch('data_acquisition.yf.Ticker')
    def test_descargar_datos_exitoso(self, mock_ticker, sample_ticker, date_range):
        """Test de descarga exitosa de datos."""
        # Configurar mock
        mock_ticker_instance = MagicMock()
        mock_ticker.return_value = mock_ticker_instance

        # Crear datos de prueba
        dates = pd.date_range(start=date_range[0], end=date_range[1], freq='D')
        mock_data = pd.DataFrame({
            'Open': [150.0] * len(dates),
            'High': [152.0] * len(dates),
            'Low': [149.0] * len(dates),
            'Close': [151.0] * len(dates),
            'Volume': [1000000] * len(dates)
        }, index=dates)

        mock_ticker_instance.history.return_value = mock_data
        mock_ticker_instance.info = {'longName': 'Apple Inc.'}

        # Ejecutar
        datos, company_name = data_acquisition.descargar_datos(
            sample_ticker, date_range[0], date_range[1]
        )

        # Verificar
        assert datos is not None
        assert isinstance(datos, pd.DataFrame)
        assert len(datos) > 0
        assert 'fecha' in datos.columns
        assert 'apertura' in datos.columns
        assert 'cierre' in datos.columns
        assert company_name == 'Apple Inc.'

    @patch('data_acquisition.yf.Ticker')
    def test_descargar_datos_sin_nombre_empresa(self, mock_ticker, sample_ticker, date_range):
        """Test cuando no se puede obtener el nombre de la empresa."""
        mock_ticker_instance = MagicMock()
        mock_ticker.return_value = mock_ticker_instance

        dates = pd.date_range(start=date_range[0], end=date_range[1], freq='D')
        mock_data = pd.DataFrame({
            'Open': [150.0] * len(dates),
            'High': [152.0] * len(dates),
            'Low': [149.0] * len(dates),
            'Close': [151.0] * len(dates),
            'Volume': [1000000] * len(dates)
        }, index=dates)

        mock_ticker_instance.history.return_value = mock_data
        mock_ticker_instance.info = {}  # Sin longName

        datos, company_name = data_acquisition.descargar_datos(
            sample_ticker, date_range[0], date_range[1]
        )

        assert datos is not None
        assert company_name == sample_ticker  # Debe usar el ticker como nombre

    @patch('data_acquisition.yf.Ticker')
    def test_descargar_datos_sin_datos(self, mock_ticker, sample_ticker, date_range):
        """Test cuando no se obtienen datos del ticker."""
        mock_ticker_instance = MagicMock()
        mock_ticker.return_value = mock_ticker_instance

        # Datos vacíos
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker_instance.info = {}

        datos, company_name = data_acquisition.descargar_datos(
            sample_ticker, date_range[0], date_range[1]
        )

        assert datos is None
        assert company_name is None

    @patch('data_acquisition.yf.Ticker')
    def test_descargar_datos_con_error(self, mock_ticker, sample_ticker, date_range):
        """Test cuando hay un error durante la descarga."""
        mock_ticker.side_effect = Exception("Error de conexión")

        datos, company_name = data_acquisition.descargar_datos(
            sample_ticker, date_range[0], date_range[1]
        )

        assert datos is None
        assert company_name is None


class TestConCache:
    """Tests para la integración con caché."""

    @patch('data_acquisition.cache_manager')
    @patch('data_acquisition.yf.Ticker')
    def test_usa_cache_cuando_esta_disponible(self, mock_ticker, mock_cache,
                                               sample_ticker, date_range,
                                               sample_historical_data):
        """Test que verifica que se usa el caché cuando está disponible."""
        # Configurar caché para retornar datos
        mock_cache.get.return_value = (sample_historical_data, 'Apple Inc.')

        datos, company_name = data_acquisition.descargar_datos(
            sample_ticker, date_range[0], date_range[1]
        )

        # Verificar que se usó el caché
        mock_cache.get.assert_called_once()
        # No debería llamar a yfinance
        mock_ticker.assert_not_called()
        assert datos is not None
        assert company_name == 'Apple Inc.'

    @patch('data_acquisition.cache_manager')
    @patch('data_acquisition.yf.Ticker')
    def test_descarga_cuando_cache_no_disponible(self, mock_ticker, mock_cache,
                                                  sample_ticker, date_range):
        """Test que descarga datos cuando el caché no está disponible."""
        # Configurar caché vacío
        mock_cache.get.return_value = None

        # Configurar mock de yfinance
        mock_ticker_instance = MagicMock()
        mock_ticker.return_value = mock_ticker_instance

        dates = pd.date_range(start=date_range[0], end=date_range[1], freq='D')
        mock_data = pd.DataFrame({
            'Open': [150.0] * len(dates),
            'High': [152.0] * len(dates),
            'Low': [149.0] * len(dates),
            'Close': [151.0] * len(dates),
            'Volume': [1000000] * len(dates)
        }, index=dates)

        mock_ticker_instance.history.return_value = mock_data
        mock_ticker_instance.info = {'longName': 'Apple Inc.'}

        datos, company_name = data_acquisition.descargar_datos(
            sample_ticker, date_range[0], date_range[1]
        )

        # Verificar que intentó usar caché
        mock_cache.get.assert_called_once()
        # Debería haber descargado
        mock_ticker.assert_called_once()
        # Debería guardar en caché
        mock_cache.set.assert_called_once()
        assert datos is not None
