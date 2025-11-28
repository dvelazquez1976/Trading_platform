"""
Tests para el módulo data_storage.
"""

import pytest
import pandas as pd
import sqlite3
import data_storage
from unittest.mock import patch


class TestGuardarDatos:
    """Tests para la función guardar_datos."""

    def test_guardar_datos_nuevos(self, sample_historical_data, sample_ticker, temp_db_path):
        """Test de guardado de datos nuevos en la base de datos."""
        with patch('data_storage.DB_PATH', temp_db_path):
            # Guardar datos
            data_storage.guardar_datos(sample_historical_data, sample_ticker)

            # Verificar que se guardaron
            datos_leidos = data_storage.leer_datos(sample_ticker)

            assert datos_leidos is not None
            assert len(datos_leidos) == len(sample_historical_data)
            assert 'fecha' in datos_leidos.columns
            assert 'cierre' in datos_leidos.columns

    def test_actualizar_datos_existentes(self, sample_historical_data, sample_ticker, temp_db_path):
        """Test de actualización de datos existentes."""
        with patch('data_storage.DB_PATH', temp_db_path):
            # Guardar datos iniciales
            data_storage.guardar_datos(sample_historical_data, sample_ticker)

            # Modificar datos
            modified_data = sample_historical_data.copy()
            modified_data['cierre'] = modified_data['cierre'] * 1.1

            # Guardar datos modificados
            data_storage.guardar_datos(modified_data, sample_ticker)

            # Verificar actualización
            datos_leidos = data_storage.leer_datos(sample_ticker)

            assert len(datos_leidos) == len(sample_historical_data)
            # Verificar que los valores fueron actualizados
            assert datos_leidos['cierre'].iloc[0] == pytest.approx(modified_data['cierre'].iloc[0])

    def test_guardar_datos_vacios(self, sample_ticker, temp_db_path):
        """Test de guardar un DataFrame vacío."""
        with patch('data_storage.DB_PATH', temp_db_path):
            empty_df = pd.DataFrame()

            # No debería fallar con DataFrame vacío
            data_storage.guardar_datos(empty_df, sample_ticker)


class TestLeerDatos:
    """Tests para la función leer_datos."""

    def test_leer_datos_existentes(self, sample_historical_data, sample_ticker, temp_db_path):
        """Test de lectura de datos existentes."""
        with patch('data_storage.DB_PATH', temp_db_path):
            # Primero guardar datos
            data_storage.guardar_datos(sample_historical_data, sample_ticker)

            # Leer datos
            datos_leidos = data_storage.leer_datos(sample_ticker)

            assert datos_leidos is not None
            assert isinstance(datos_leidos, pd.DataFrame)
            assert len(datos_leidos) > 0
            assert 'fecha' in datos_leidos.columns
            # Verificar que las fechas son datetime
            assert pd.api.types.is_datetime64_any_dtype(datos_leidos['fecha'])

    def test_leer_datos_inexistentes(self, temp_db_path):
        """Test de lectura de ticker que no existe."""
        with patch('data_storage.DB_PATH', temp_db_path):
            datos = data_storage.leer_datos('TICKER_INEXISTENTE')

            # Debería retornar DataFrame vacío
            assert datos is not None
            assert isinstance(datos, pd.DataFrame)
            assert len(datos) == 0

    def test_leer_datos_ordenados_por_fecha(self, sample_historical_data, sample_ticker, temp_db_path):
        """Test que verifica que los datos se leen ordenados por fecha."""
        with patch('data_storage.DB_PATH', temp_db_path):
            # Guardar datos
            data_storage.guardar_datos(sample_historical_data, sample_ticker)

            # Leer datos
            datos = data_storage.leer_datos(sample_ticker)

            # Verificar orden
            assert datos['fecha'].is_monotonic_increasing


class TestContarRegistros:
    """Tests para la función contar_registros."""

    def test_contar_todos_registros(self, sample_historical_data, sample_ticker, temp_db_path):
        """Test de contar todos los registros en la base de datos."""
        with patch('data_storage.DB_PATH', temp_db_path):
            # Guardar datos para un ticker
            data_storage.guardar_datos(sample_historical_data, sample_ticker)

            # Contar todos los registros
            total = data_storage.contar_registros()

            assert total == len(sample_historical_data)

    def test_contar_registros_ticker_especifico(self, sample_historical_data, sample_ticker, temp_db_path):
        """Test de contar registros de un ticker específico."""
        with patch('data_storage.DB_PATH', temp_db_path):
            # Guardar datos
            data_storage.guardar_datos(sample_historical_data, sample_ticker)

            # Contar para ese ticker
            count = data_storage.contar_registros(sample_ticker)

            assert count == len(sample_historical_data)

    def test_contar_registros_ticker_inexistente(self, temp_db_path):
        """Test de contar registros de ticker inexistente."""
        with patch('data_storage.DB_PATH', temp_db_path):
            count = data_storage.contar_registros('TICKER_INEXISTENTE')

            assert count == 0


class TestEliminarTicker:
    """Tests para la función eliminar_ticker."""

    def test_eliminar_ticker_existente(self, sample_historical_data, sample_ticker, temp_db_path):
        """Test de eliminación de ticker existente."""
        with patch('data_storage.DB_PATH', temp_db_path):
            # Guardar datos
            data_storage.guardar_datos(sample_historical_data, sample_ticker)

            # Verificar que existen
            assert data_storage.contar_registros(sample_ticker) > 0

            # Eliminar
            data_storage.eliminar_ticker(sample_ticker)

            # Verificar eliminación
            assert data_storage.contar_registros(sample_ticker) == 0

    def test_eliminar_ticker_inexistente(self, temp_db_path):
        """Test de eliminación de ticker que no existe."""
        with patch('data_storage.DB_PATH', temp_db_path):
            # No debería fallar al eliminar ticker inexistente
            data_storage.eliminar_ticker('TICKER_INEXISTENTE')


class TestCrearTabla:
    """Tests para la función crear_tabla."""

    def test_crear_tabla(self, temp_db_path):
        """Test de creación de tabla."""
        with patch('data_storage.DB_PATH', temp_db_path):
            data_storage.crear_tabla()

            # Verificar que la tabla existe
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='datos_historicos'
            """)
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            assert result[0] == 'datos_historicos'

    def test_crear_tabla_ya_existente(self, temp_db_path):
        """Test de crear tabla cuando ya existe."""
        with patch('data_storage.DB_PATH', temp_db_path):
            # Crear tabla dos veces
            data_storage.crear_tabla()
            data_storage.crear_tabla()  # No debería fallar

            # Verificar que la tabla existe
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='datos_historicos'
            """)
            result = cursor.fetchone()
            conn.close()

            assert result is not None
