"""
Interfaz de Línea de Comandos (CLI)
====================================

Proporciona una interfaz amigable para ejecutar la plataforma de trading
con diferentes opciones y configuraciones.
"""

import argparse
import sys
from pathlib import Path
from logger_config import get_logger
from cache_manager import get_cache_manager

logger = get_logger(__name__)


class TradingCLI:
    """Gestiona la interfaz de línea de comandos."""

    def __init__(self):
        """Inicializa el CLI."""
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """
        Crea el parser de argumentos de línea de comandos.

        Returns:
            ArgumentParser configurado
        """
        parser = argparse.ArgumentParser(
            description='Plataforma de Análisis Técnico de Trading',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''
Ejemplos de uso:
  # Ejecución básica
  python cli.py

  # Con archivo de tickers personalizado
  python cli.py --tickers mis_tickers.txt

  # Análisis de los últimos 365 días
  python cli.py --days 365

  # Modo paralelo con 8 workers
  python cli.py --parallel --workers 8

  # Habilitar indicadores avanzados
  python cli.py --advanced

  # Limpiar caché antes de ejecutar
  python cli.py --clear-cache

  # Ver estadísticas de caché
  python cli.py --cache-stats

  # Modo backtesting
  python cli.py --backtest --strategy ma_crossover --capital 10000
            '''
        )

        # Grupo: Configuración de datos
        data_group = parser.add_argument_group('Configuración de Datos')
        data_group.add_argument(
            '--tickers', '-t',
            type=str,
            default='tickers.txt',
            help='Archivo con la lista de tickers (default: tickers.txt)'
        )
        data_group.add_argument(
            '--days', '-d',
            type=int,
            help='Número de días de histórico a analizar (default: config.json)'
        )

        # Grupo: Procesamiento
        proc_group = parser.add_argument_group('Procesamiento')
        proc_group.add_argument(
            '--parallel', '-p',
            action='store_true',
            help='Activar procesamiento paralelo'
        )
        proc_group.add_argument(
            '--workers', '-w',
            type=int,
            help='Número de workers para procesamiento paralelo (default: 4)'
        )

        # Grupo: Indicadores
        ind_group = parser.add_argument_group('Indicadores')
        ind_group.add_argument(
            '--advanced', '-a',
            action='store_true',
            help='Habilitar indicadores técnicos avanzados'
        )

        # Grupo: Caché
        cache_group = parser.add_argument_group('Gestión de Caché')
        cache_group.add_argument(
            '--clear-cache',
            action='store_true',
            help='Limpiar todo el caché antes de ejecutar'
        )
        cache_group.add_argument(
            '--clear-cache-ticker',
            type=str,
            metavar='TICKER',
            help='Limpiar caché solo para un ticker específico'
        )
        cache_group.add_argument(
            '--cache-stats',
            action='store_true',
            help='Mostrar estadísticas del caché y salir'
        )
        cache_group.add_argument(
            '--no-cache',
            action='store_true',
            help='Desactivar uso de caché para esta ejecución'
        )

        # Grupo: Backtesting
        backtest_group = parser.add_argument_group('Backtesting')
        backtest_group.add_argument(
            '--backtest', '-b',
            action='store_true',
            help='Ejecutar modo backtesting'
        )
        backtest_group.add_argument(
            '--strategy',
            type=str,
            choices=['ma_crossover', 'rsi_threshold', 'macd_signal', 'multi_indicator'],
            help='Estrategia de backtesting a usar'
        )
        backtest_group.add_argument(
            '--capital',
            type=float,
            default=10000.0,
            help='Capital inicial para backtesting (default: 10000)'
        )

        # Grupo: Salida
        output_group = parser.add_argument_group('Configuración de Salida')
        output_group.add_argument(
            '--output-dir', '-o',
            type=str,
            default='salidas',
            help='Directorio de salida para archivos generados (default: salidas)'
        )
        output_group.add_argument(
            '--no-html',
            action='store_true',
            help='No generar gráficos HTML'
        )
        output_group.add_argument(
            '--no-csv',
            action='store_true',
            help='No generar archivos CSV'
        )

        # Otras opciones
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Modo verbose (más detalles en logs)'
        )
        parser.add_argument(
            '--version',
            action='version',
            version='Plataforma de Trading v2.0.0'
        )

        return parser

    def run(self, args=None):
        """
        Ejecuta el CLI con los argumentos proporcionados.

        Args:
            args: Lista de argumentos (None usa sys.argv)
        """
        parsed_args = self.parser.parse_args(args)

        # Configurar nivel de logging si verbose
        if parsed_args.verbose:
            logger.info("Modo verbose activado")

        # Gestión de caché
        cache_manager = get_cache_manager()

        if parsed_args.cache_stats:
            self._show_cache_stats(cache_manager)
            return

        if parsed_args.clear_cache:
            logger.info("Limpiando todo el caché...")
            cache_manager.clear()

        if parsed_args.clear_cache_ticker:
            logger.info(f"Limpiando caché para {parsed_args.clear_cache_ticker}...")
            cache_manager.clear(parsed_args.clear_cache_ticker)

        # Modo backtesting
        if parsed_args.backtest:
            self._run_backtest(parsed_args)
            return

        # Modo normal - análisis técnico
        self._run_analysis(parsed_args)

    def _show_cache_stats(self, cache_manager):
        """
        Muestra estadísticas del caché.

        Args:
            cache_manager: Instancia de CacheManager
        """
        stats = cache_manager.get_stats()

        print("\n" + "="*60)
        print("ESTADÍSTICAS DE CACHÉ")
        print("="*60)
        print(f"Directorio: {stats['cache_dir']}")
        print(f"Total de archivos: {stats['total_files']}")
        print(f"  Válidos: {stats['valid_files']}")
        print(f"  Expirados: {stats['expired_files']}")
        print(f"Tamaño total: {stats['total_size_mb']:.2f} MB")
        print("="*60 + "\n")

    def _run_backtest(self, args):
        """
        Ejecuta modo backtesting.

        Args:
            args: Argumentos parseados
        """
        logger.info("="*80)
        logger.info("MODO BACKTESTING")
        logger.info("="*80)

        if not args.strategy:
            logger.error("Debe especificar una estrategia con --strategy")
            self.parser.print_help()
            sys.exit(1)

        try:
            from backtesting_engine import BacktestingEngine

            engine = BacktestingEngine(
                tickers_file=args.tickers,
                strategy=args.strategy,
                initial_capital=args.capital,
                days=args.days
            )

            results = engine.run()

            # Mostrar resultados
            print("\n" + "="*80)
            print("RESULTADOS DE BACKTESTING")
            print("="*80)
            print(f"Estrategia: {args.strategy}")
            print(f"Capital inicial: ${args.capital:,.2f}")
            print(f"Capital final: ${results['final_capital']:,.2f}")
            print(f"Retorno total: {results['total_return']:.2f}%")
            print(f"Número de operaciones: {results['num_trades']}")
            print(f"Operaciones ganadoras: {results['winning_trades']}")
            print(f"Operaciones perdedoras: {results['losing_trades']}")
            print(f"Win rate: {results['win_rate']:.2f}%")
            print("="*80 + "\n")

            logger.info("Backtesting completado exitosamente")

        except ImportError:
            logger.error("Módulo de backtesting no disponible")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error durante backtesting: {e}", exc_info=True)
            sys.exit(1)

    def _run_analysis(self, args):
        """
        Ejecuta análisis técnico normal.

        Args:
            args: Argumentos parseados
        """
        logger.info("="*80)
        logger.info("MODO ANÁLISIS TÉCNICO")
        logger.info("="*80)

        try:
            from main import TradingPlatform
            from config_manager import config_manager

            # Actualizar configuración basada en argumentos CLI
            if args.days:
                config_manager.update('data', 'analysis_period_days', args.days)
                logger.info(f"Período de análisis configurado: {args.days} días")

            if args.parallel:
                config_manager.update('processing', 'parallel_processing', True)
                logger.info("Procesamiento paralelo activado")

            if args.workers:
                config_manager.update('processing', 'max_workers', args.workers)
                logger.info(f"Workers configurados: {args.workers}")

            if args.advanced:
                config_manager.update('advanced_indicators', 'enabled', True)
                logger.info("Indicadores avanzados activados")

            # Crear y ejecutar plataforma
            platform = TradingPlatform()

            # Aplicar configuraciones CLI
            if args.tickers != 'tickers.txt':
                platform.tickers_file = args.tickers

            platform.salidas_dir = args.output_dir
            platform.generate_html = not args.no_html
            platform.generate_csv = not args.no_csv
            platform.use_cache = not args.no_cache

            # Ejecutar
            platform.run()

            logger.info("Análisis completado exitosamente")

        except Exception as e:
            logger.error(f"Error durante la ejecución: {e}", exc_info=True)
            sys.exit(1)


def main():
    """Punto de entrada del CLI."""
    cli = TradingCLI()
    cli.run()


if __name__ == "__main__":
    main()
