"""
Motor de Backtesting
====================

Prueba estrategias de trading con datos históricos.
Calcula métricas de rendimiento y genera reportes.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Callable
from datetime import datetime
from logger_config import get_logger
import data_acquisition
import indicator_calculator
import signal_generator

logger = get_logger(__name__)


class Trade:
    """Representa una operación individual."""

    def __init__(self, ticker: str, entry_date: datetime, entry_price: float,
                 position_size: int, trade_type: str):
        """
        Inicializa una operación.

        Args:
            ticker: Símbolo del activo
            entry_date: Fecha de entrada
            entry_price: Precio de entrada
            position_size: Cantidad de acciones
            trade_type: 'LONG' o 'SHORT'
        """
        self.ticker = ticker
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.position_size = position_size
        self.trade_type = trade_type
        self.exit_date = None
        self.exit_price = None
        self.profit_loss = 0.0
        self.profit_loss_pct = 0.0

    def close(self, exit_date: datetime, exit_price: float):
        """Cierra la operación."""
        self.exit_date = exit_date
        self.exit_price = exit_price

        if self.trade_type == 'LONG':
            self.profit_loss = (exit_price - self.entry_price) * self.position_size
        else:  # SHORT
            self.profit_loss = (self.entry_price - exit_price) * self.position_size

        self.profit_loss_pct = (self.profit_loss / (self.entry_price * self.position_size)) * 100

    def is_open(self) -> bool:
        """Verifica si la operación está abierta."""
        return self.exit_date is None


class BacktestingEngine:
    """Motor principal de backtesting."""

    def __init__(self, tickers_file: str = 'tickers.txt', strategy: str = 'ma_crossover',
                 initial_capital: float = 10000.0, days: int = None):
        """
        Inicializa el motor de backtesting.

        Args:
            tickers_file: Archivo con lista de tickers
            strategy: Estrategia a probar
            initial_capital: Capital inicial
            days: Días de histórico (None = config default)
        """
        self.tickers_file = tickers_file
        self.strategy_name = strategy
        self.initial_capital = initial_capital
        self.days = days
        self.trades: List[Trade] = []
        self.equity_curve = []

        logger.info(f"Backtesting Engine inicializado: {strategy}, capital=${initial_capital}")

    def _load_tickers(self) -> List[str]:
        """Carga lista de tickers."""
        try:
            with open(self.tickers_file, 'r') as f:
                tickers = [line.strip() for line in f if line.strip()]
            logger.info(f"Cargados {len(tickers)} tickers para backtesting")
            return tickers
        except Exception as e:
            logger.error(f"Error cargando tickers: {e}")
            return []

    def _get_strategy_func(self) -> Callable:
        """Obtiene función de estrategia."""
        strategies = {
            'ma_crossover': self._strategy_ma_crossover,
            'rsi_threshold': self._strategy_rsi_threshold,
            'macd_signal': self._strategy_macd_signal,
            'multi_indicator': self._strategy_multi_indicator
        }
        return strategies.get(self.strategy_name, self._strategy_ma_crossover)

    def _strategy_ma_crossover(self, row, prev_row) -> str:
        """
        Estrategia: Cruce de medias móviles.

        Returns:
            'BUY', 'SELL', o 'HOLD'
        """
        if pd.isna(row['SMA_30']) or pd.isna(row['SMA_60']):
            return 'HOLD'

        # Cruce alcista
        if row['SMA_30'] > row['SMA_60'] and prev_row['SMA_30'] <= prev_row['SMA_60']:
            return 'BUY'

        # Cruce bajista
        if row['SMA_30'] < row['SMA_60'] and prev_row['SMA_30'] >= prev_row['SMA_60']:
            return 'SELL'

        return 'HOLD'

    def _strategy_rsi_threshold(self, row, prev_row) -> str:
        """Estrategia: RSI con umbrales."""
        if pd.isna(row['RSI']):
            return 'HOLD'

        if row['RSI'] < 30:  # Sobreventa
            return 'BUY'
        elif row['RSI'] > 70:  # Sobrecompra
            return 'SELL'

        return 'HOLD'

    def _strategy_macd_signal(self, row, prev_row) -> str:
        """Estrategia: Señales MACD."""
        if pd.isna(row['MACD_12_26_9']) or pd.isna(row['MACDs_12_26_9']):
            return 'HOLD'

        # Cruce alcista
        if row['MACD_12_26_9'] > row['MACDs_12_26_9'] and \
           prev_row['MACD_12_26_9'] <= prev_row['MACDs_12_26_9']:
            return 'BUY'

        # Cruce bajista
        if row['MACD_12_26_9'] < row['MACDs_12_26_9'] and \
           prev_row['MACD_12_26_9'] >= prev_row['MACDs_12_26_9']:
            return 'SELL'

        return 'HOLD'

    def _strategy_multi_indicator(self, row, prev_row) -> str:
        """Estrategia: Múltiples indicadores (votación)."""
        signals = []

        # RSI
        if not pd.isna(row['RSI']):
            if row['RSI'] < 30:
                signals.append('BUY')
            elif row['RSI'] > 70:
                signals.append('SELL')

        # MACD
        if not pd.isna(row['MACD_12_26_9']):
            if row['MACD_12_26_9'] > row['MACDs_12_26_9']:
                signals.append('BUY')
            else:
                signals.append('SELL')

        # Medias Móviles
        if not pd.isna(row['SMA_30']):
            if row['SMA_30'] > row['SMA_60']:
                signals.append('BUY')
            else:
                signals.append('SELL')

        # Votación por mayoría
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')

        if buy_count > sell_count:
            return 'BUY'
        elif sell_count > buy_count:
            return 'SELL'

        return 'HOLD'

    def _simulate_ticker(self, ticker: str, datos: pd.DataFrame) -> List[Trade]:
        """
        Simula trading en un ticker.

        Args:
            ticker: Símbolo del ticker
            datos: DataFrame con datos e indicadores

        Returns:
            Lista de operaciones realizadas
        """
        strategy_func = self._get_strategy_func()
        ticker_trades = []
        current_position = None
        position_value_pct = 0.25  # 25% del capital por operación

        for i in range(1, len(datos)):
            row = datos.iloc[i]
            prev_row = datos.iloc[i-1]

            signal = strategy_func(row, prev_row)

            # Si no hay posición y señal de compra
            if current_position is None and signal == 'BUY':
                position_value = self.initial_capital * position_value_pct
                position_size = int(position_value / row['cierre'])

                if position_size > 0:
                    current_position = Trade(
                        ticker=ticker,
                        entry_date=row['fecha'],
                        entry_price=row['cierre'],
                        position_size=position_size,
                        trade_type='LONG'
                    )
                    logger.debug(
                        f"OPEN {ticker}: {position_size} @ ${row['cierre']:.2f} "
                        f"on {row['fecha'].date()}"
                    )

            # Si hay posición abierta y señal de venta
            elif current_position is not None and signal == 'SELL':
                current_position.close(row['fecha'], row['cierre'])
                ticker_trades.append(current_position)

                logger.debug(
                    f"CLOSE {ticker}: P/L ${current_position.profit_loss:.2f} "
                    f"({current_position.profit_loss_pct:.2f}%) on {row['fecha'].date()}"
                )

                current_position = None

        # Cerrar posición abierta al final
        if current_position is not None:
            last_row = datos.iloc[-1]
            current_position.close(last_row['fecha'], last_row['cierre'])
            ticker_trades.append(current_position)
            logger.debug(f"CLOSE {ticker} (end): P/L ${current_position.profit_loss:.2f}")

        return ticker_trades

    def run(self) -> Dict:
        """
        Ejecuta el backtesting.

        Returns:
            Diccionario con resultados
        """
        logger.info("Iniciando backtesting...")

        tickers = self._load_tickers()
        if not tickers:
            logger.error("No se cargaron tickers")
            return {}

        all_trades = []

        for ticker in tickers:
            logger.info(f"Backtesting en {ticker}...")

            # Descargar datos
            from datetime import date, timedelta
            fecha_fin = date.today()
            days = self.days or 730
            fecha_inicio = fecha_fin - timedelta(days=days)

            datos, _ = data_acquisition.descargar_datos(
                ticker,
                fecha_inicio.strftime("%Y-%m-%d"),
                fecha_fin.strftime("%Y-%m-%d")
            )

            if datos is None or datos.empty:
                logger.warning(f"No hay datos para {ticker}")
                continue

            # Calcular indicadores
            datos['ticker'] = ticker
            datos_con_ind = indicator_calculator.calcular_indicadores(datos)
            datos_con_ind.dropna(inplace=True)

            if len(datos_con_ind) < 2:
                logger.warning(f"Datos insuficientes para {ticker}")
                continue

            # Simular trading
            ticker_trades = self._simulate_ticker(ticker, datos_con_ind)
            all_trades.extend(ticker_trades)

        # Calcular métricas
        results = self._calculate_metrics(all_trades)

        logger.info("Backtesting completado")
        return results

    def _calculate_metrics(self, trades: List[Trade]) -> Dict:
        """Calcula métricas de rendimiento."""
        if not trades:
            return {
                'final_capital': self.initial_capital,
                'total_return': 0.0,
                'num_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0
            }

        total_profit_loss = sum(t.profit_loss for t in trades)
        final_capital = self.initial_capital + total_profit_loss

        winning_trades = [t for t in trades if t.profit_loss > 0]
        losing_trades = [t for t in trades if t.profit_loss < 0]

        win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0

        return {
            'final_capital': final_capital,
            'total_return': ((final_capital - self.initial_capital) / self.initial_capital) * 100,
            'num_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'average_win': np.mean([t.profit_loss for t in winning_trades]) if winning_trades else 0,
            'average_loss': np.mean([t.profit_loss for t in losing_trades]) if losing_trades else 0,
            'largest_win': max([t.profit_loss for t in trades]) if trades else 0,
            'largest_loss': min([t.profit_loss for t in trades]) if trades else 0
        }
