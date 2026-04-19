"""Motor de backtesting con costes realistas y métricas de riesgo."""

import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from trading_platform.core.config import config_manager
from trading_platform.core.logging import get_logger
from trading_platform.backtesting.costs import TransactionCosts
from trading_platform.backtesting.metrics import calculate_metrics

logger = get_logger(__name__)

STRATEGIES = ["sma_crossover", "rsi_oversold", "macd_signal", "bollinger_reversion"]


@dataclass
class Trade:
    ticker: str
    entry_date: object
    entry_price: float
    position_size: int
    trade_type: str = 'LONG'
    exit_date: object = None
    exit_price: float = None
    cost_entry: float = 0.0
    cost_exit:  float = 0.0
    profit_loss: float = field(init=False, default=0.0)
    profit_loss_pct: float = field(init=False, default=0.0)

    def close(self, exit_date, exit_price: float, cost: float = 0.0):
        self.exit_date  = exit_date
        self.exit_price = exit_price
        self.cost_exit  = cost
        gross = (exit_price - self.entry_price) * self.position_size
        total_costs = self.cost_entry + self.cost_exit
        self.profit_loss = gross - total_costs
        invested = self.entry_price * self.position_size
        self.profit_loss_pct = (self.profit_loss / invested) * 100 if invested else 0


class BacktestingEngine:
    def __init__(self, strategy: str = 'sma_crossover', initial_capital: float = 10_000.0,
                 days: int = 730, transaction_costs: TransactionCosts = None):
        if strategy not in STRATEGIES:
            raise ValueError(f"Estrategia '{strategy}' no reconocida. Opciones: {STRATEGIES}")
        self.strategy_name   = strategy
        self.initial_capital = initial_capital
        self.days = days
        self.costs = transaction_costs or TransactionCosts.from_config(config_manager.config)
        logger.info(f"BacktestingEngine: {strategy}, capital={initial_capital}")

    def run(self, tickers: List[str]) -> Dict:
        """Descarga datos internamente y ejecuta el backtest sobre una lista de tickers."""
        from trading_platform.providers import descargar_datos
        from trading_platform.indicators.basic import calcular_indicadores

        all_trades = []
        fecha_fin    = date.today()
        fecha_inicio = fecha_fin - timedelta(days=self.days)

        for ticker in tickers:
            datos, _ = descargar_datos(
                ticker, fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d'))
            if datos is None or datos.empty:
                continue
            datos['ticker'] = ticker
            df = calcular_indicadores(datos)
            df.dropna(inplace=True)
            if len(df) < 2:
                continue
            all_trades.extend(self._simulate(ticker, df))

        metrics = calculate_metrics(all_trades, self.initial_capital, self.days)
        return {
            'metrics': metrics,
            'trades': [self._trade_to_dict(t) for t in all_trades],
            'equity_curve': self._equity_curve(all_trades),
        }

    def run_on_df(self, df: pd.DataFrame) -> Dict:
        """Ejecuta el backtest sobre un DataFrame ya descargado con indicadores."""
        ticker = df['ticker'].iloc[0] if 'ticker' in df.columns else 'TICKER'
        trades = self._simulate(ticker, df)
        metrics = calculate_metrics(trades, self.initial_capital, self.days)
        return {
            'metrics': metrics,
            'trades': [self._trade_to_dict(t) for t in trades],
            'equity_curve': self._equity_curve(trades),
        }

    # ── Simulación ─────────────────────────────────────────────────────────

    def _simulate(self, ticker: str, datos: pd.DataFrame) -> List[Trade]:
        fn = getattr(self, f'_strategy_{self.strategy_name}')
        trades = []
        position = None
        size_pct = 0.25

        for i in range(1, len(datos)):
            row, prev = datos.iloc[i], datos.iloc[i - 1]
            signal = fn(row, prev)

            if position is None and signal == 'BUY':
                value = self.initial_capital * size_pct
                n = int(value / row['cierre'])
                if n > 0:
                    cost = self.costs.apply(n * row['cierre'])
                    position = Trade(ticker, row['fecha'], row['cierre'], n, cost_entry=cost)

            elif position is not None and signal == 'SELL':
                cost = self.costs.apply(position.position_size * row['cierre'])
                position.close(row['fecha'], row['cierre'], cost)
                trades.append(position)
                position = None

        if position is not None:
            last = datos.iloc[-1]
            cost = self.costs.apply(position.position_size * last['cierre'])
            position.close(last['fecha'], last['cierre'], cost)
            trades.append(position)

        return trades

    # ── Estrategias ────────────────────────────────────────────────────────

    def _strategy_sma_crossover(self, row, prev) -> str:
        if pd.isna(row.get('SMA_30')) or pd.isna(row.get('SMA_60')): return 'HOLD'
        if row['SMA_30'] > row['SMA_60'] and prev['SMA_30'] <= prev['SMA_60']: return 'BUY'
        if row['SMA_30'] < row['SMA_60'] and prev['SMA_30'] >= prev['SMA_60']: return 'SELL'
        return 'HOLD'

    def _strategy_rsi_oversold(self, row, prev) -> str:
        if pd.isna(row.get('RSI')): return 'HOLD'
        if row['RSI'] < 30: return 'BUY'
        if row['RSI'] > 70: return 'SELL'
        return 'HOLD'

    def _strategy_macd_signal(self, row, prev) -> str:
        if pd.isna(row.get('MACD')) or pd.isna(row.get('MACDs')): return 'HOLD'
        if row['MACD'] > row['MACDs'] and prev['MACD'] <= prev['MACDs']: return 'BUY'
        if row['MACD'] < row['MACDs'] and prev['MACD'] >= prev['MACDs']: return 'SELL'
        return 'HOLD'

    def _strategy_bollinger_reversion(self, row, prev) -> str:
        if pd.isna(row.get('BBL_BB')) or pd.isna(row.get('BBU_BB')): return 'HOLD'
        if row['cierre'] < row['BBL_BB']: return 'BUY'
        if row['cierre'] > row['BBU_BB']: return 'SELL'
        return 'HOLD'

    # ── Helpers ────────────────────────────────────────────────────────────

    def _trade_to_dict(self, t: Trade) -> dict:
        return {
            'ticker':       t.ticker,
            'entry_date':   str(t.entry_date),
            'exit_date':    str(t.exit_date),
            'entry_price':  t.entry_price,
            'exit_price':   t.exit_price,
            'shares':       t.position_size,
            'pnl':          round(t.profit_loss, 2),
            'return_pct':   round(t.profit_loss_pct, 2),
        }

    def _equity_curve(self, trades: List[Trade]) -> list:
        equity = self.initial_capital
        curve = [{'date': str(date.today() - timedelta(days=self.days)), 'equity': equity}]
        for t in trades:
            equity += t.profit_loss
            curve.append({'date': str(t.exit_date), 'equity': round(equity, 2)})
        return curve
