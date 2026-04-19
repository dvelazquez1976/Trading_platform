"""Métricas de rendimiento para backtesting."""

import numpy as np
from typing import List


def calculate_metrics(trades: list, initial_capital: float, total_days: int) -> dict:
    if not trades:
        return _empty(initial_capital)

    pnl = [t.profit_loss for t in trades]
    total_pnl = sum(pnl)
    final_capital = initial_capital + total_pnl
    total_return = (final_capital - initial_capital) / initial_capital

    winners = [t for t in trades if t.profit_loss > 0]
    losers  = [t for t in trades if t.profit_loss < 0]

    # CAGR
    years = max(total_days / 365, 0.01)
    cagr = (1 + total_return) ** (1 / years) - 1

    # Sharpe (risk-free rate 2% anual)
    if len(pnl) > 1:
        returns_pct = [p / initial_capital for p in pnl]
        risk_free_daily = 0.02 / 252
        excess = [r - risk_free_daily for r in returns_pct]
        sharpe = (np.mean(excess) / (np.std(excess) + 1e-9)) * np.sqrt(252)
    else:
        sharpe = 0.0

    # Sortino
    if len(pnl) > 1:
        neg_returns = [r for r in [p / initial_capital for p in pnl] if r < 0]
        downside_std = np.std(neg_returns) if len(neg_returns) > 1 else 1e-9
        sortino = (np.mean([p / initial_capital for p in pnl]) / downside_std) * np.sqrt(252)
    else:
        sortino = 0.0

    # Max drawdown (sobre la equity curve de trades)
    equity = [initial_capital]
    for p in pnl:
        equity.append(equity[-1] + p)
    peak = equity[0]
    max_dd = 0.0
    for e in equity:
        if e > peak:
            peak = e
        dd = (peak - e) / peak
        if dd > max_dd:
            max_dd = dd

    # Profit factor
    gross_profit = sum(p for p in pnl if p > 0)
    gross_loss   = abs(sum(p for p in pnl if p < 0))
    profit_factor = gross_profit / gross_loss if gross_loss else float('inf')

    return {
        'final_capital':    round(final_capital, 2),
        'total_return_pct': round(total_return * 100, 2),
        'cagr_pct':         round(cagr * 100, 2),
        'sharpe':           round(sharpe, 3),
        'sortino':          round(sortino, 3),
        'max_drawdown_pct': round(max_dd * 100, 2),
        'profit_factor':    round(profit_factor, 3),
        'num_trades':       len(trades),
        'winning_trades':   len(winners),
        'losing_trades':    len(losers),
        'win_rate_pct':     round(len(winners) / len(trades) * 100, 1),
        'avg_win':          round(np.mean([t.profit_loss for t in winners]), 2) if winners else 0,
        'avg_loss':         round(np.mean([t.profit_loss for t in losers]),  2) if losers  else 0,
        'largest_win':      round(max(pnl), 2),
        'largest_loss':     round(min(pnl), 2),
    }


def _empty(capital: float) -> dict:
    return {
        'final_capital': capital, 'total_return_pct': 0, 'cagr_pct': 0,
        'sharpe': 0, 'sortino': 0, 'max_drawdown_pct': 0, 'profit_factor': 0,
        'num_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
        'win_rate_pct': 0, 'avg_win': 0, 'avg_loss': 0,
        'largest_win': 0, 'largest_loss': 0,
    }
