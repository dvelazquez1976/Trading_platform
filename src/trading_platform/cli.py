"""Punto de entrada CLI para ejecución sin interfaz gráfica."""

import argparse
import sys

from trading_platform.pipeline.runner import TradingPlatform


def main():
    parser = argparse.ArgumentParser(
        description="Trading Platform — análisis técnico de acciones",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--tickers', nargs='+', metavar='TICKER',
        help="Lista de tickers (ej: AAPL MSFT SAN.MC). Si se omite, usa watchlist por defecto."
    )
    parser.add_argument(
        '--days', type=int, default=730,
        help="Días de histórico a analizar (defecto: 730)"
    )
    parser.add_argument(
        '--output', metavar='DIR',
        help="Directorio de salida para informes HTML"
    )
    args = parser.parse_args()

    platform = TradingPlatform(output_dir=args.output)

    if args.tickers:
        results = platform.run_tickers(args.tickers, analysis_days=args.days)
        print(f"\n✓ Análisis completado: {len(results)} tickers procesados.")
    else:
        platform.run()


if __name__ == '__main__':
    main()
