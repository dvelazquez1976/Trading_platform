"""Tests para backtesting/engine.py, costs.py y metrics.py."""

import pytest

from trading_platform.backtesting.costs import TransactionCosts
from trading_platform.backtesting.metrics import calculate_metrics
from trading_platform.backtesting.engine import BacktestingEngine, Trade, STRATEGIES


class TestTransactionCosts:
    def test_comision_minima(self):
        tc = TransactionCosts(commission_pct=0.001, min_commission=5.0, slippage_bps=0)
        cost = tc.apply(100.0)  # 0.1% de 100 = 0.1 < mínimo 5
        assert cost == 5.0

    def test_comision_porcentual(self):
        tc = TransactionCosts(commission_pct=0.01, min_commission=0.0, slippage_bps=0)
        cost = tc.apply(10_000.0)
        assert abs(cost - 100.0) < 0.01

    def test_slippage_suma(self):
        tc = TransactionCosts(commission_pct=0.0, min_commission=0.0, slippage_bps=10)
        cost = tc.apply(10_000.0)
        assert abs(cost - 10.0) < 0.01  # 10 bps de 10000


class TestMetrics:
    def _make_trade(self, pnl: float) -> Trade:
        t = Trade("TEST", "2024-01-01", 10.0, 100)
        t.exit_date = "2024-06-01"
        t.exit_price = 10.0 + pnl / 100
        t.profit_loss = pnl
        t.profit_loss_pct = pnl / 1000 * 100
        return t

    def test_metricas_basicas(self):
        trades = [self._make_trade(50), self._make_trade(-30), self._make_trade(80)]
        m = calculate_metrics(trades, initial_capital=10_000, total_days=365)
        assert "total_return_pct" in m
        assert "sharpe" in m
        assert "max_drawdown_pct" in m
        assert "win_rate_pct" in m
        assert m["win_rate_pct"] == pytest.approx(200 / 3, abs=0.1)

    def test_sin_trades_devuelve_ceros(self):
        m = calculate_metrics([], initial_capital=10_000, total_days=365)
        assert m["num_trades"] == 0
        assert m["total_return_pct"] == 0

    def test_drawdown_no_positivo(self):
        trades = [self._make_trade(50), self._make_trade(-30), self._make_trade(80)]
        m = calculate_metrics(trades, initial_capital=10_000, total_days=365)
        assert m["max_drawdown_pct"] >= 0


class TestBacktestingEngine:
    def test_estrategia_invalida_lanza_error(self):
        with pytest.raises(ValueError, match="no reconocida"):
            BacktestingEngine(strategy="no_existe")

    @pytest.mark.parametrize("strategy", STRATEGIES)
    def test_run_on_df_devuelve_resultado(self, sample_ohlcv_with_indicators, strategy):
        engine = BacktestingEngine(strategy=strategy)
        result = engine.run_on_df(sample_ohlcv_with_indicators)
        assert "metrics" in result
        assert "trades" in result
        assert "equity_curve" in result

    @pytest.mark.parametrize("strategy", STRATEGIES)
    def test_equity_curve_empieza_con_capital_inicial(self, sample_ohlcv_with_indicators, strategy):
        engine = BacktestingEngine(strategy=strategy, initial_capital=5_000)
        result = engine.run_on_df(sample_ohlcv_with_indicators)
        assert result["equity_curve"][0]["equity"] == 5_000
