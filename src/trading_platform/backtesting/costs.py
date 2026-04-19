"""Modelo de costes de transacción para backtesting realista."""

from dataclasses import dataclass


@dataclass
class TransactionCosts:
    commission_pct: float = 0.002   # 0.20% comisión base
    min_commission: float = 1.0     # mínimo por operación en EUR/USD
    slippage_bps: float = 5.0       # 5 basis points de slippage

    def apply(self, trade_value: float) -> float:
        """Coste total para una operación de valor trade_value."""
        commission = max(trade_value * self.commission_pct, self.min_commission)
        slippage   = trade_value * (self.slippage_bps / 10_000)
        return commission + slippage

    @classmethod
    def from_config(cls, cfg: dict) -> 'TransactionCosts':
        tc = cfg.get('transaction_costs', {})
        return cls(
            commission_pct=tc.get('commission_pct', 0.002),
            min_commission=tc.get('min_commission_eur', 1.0),
            slippage_bps=tc.get('slippage_bps', 5.0),
        )
