"""Portfolio performance metrics calculation."""
import math
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

TRADING_DAYS_PER_YEAR = 252


@dataclass
class PerformanceReport:
    total_return_pct: float
    annualized_return_pct: float
    annualized_volatility_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    total_trades: int
    profitable_trades: int
    benchmark_return_pct: float    # SPY buy-and-hold
    alpha_pct: float               # strategy - benchmark

    def to_dict(self) -> dict:
        return {
            "total_return_pct": round(self.total_return_pct, 2),
            "annualized_return_pct": round(self.annualized_return_pct, 2),
            "annualized_volatility_pct": round(self.annualized_volatility_pct, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "win_rate_pct": round(self.win_rate_pct, 2),
            "total_trades": self.total_trades,
            "profitable_trades": self.profitable_trades,
            "benchmark_return_pct": round(self.benchmark_return_pct, 2),
            "alpha_pct": round(self.alpha_pct, 2),
        }

    def summary_str(self) -> str:
        return (
            f"📊 回測績效報告\n"
            f"  總報酬率        : {self.total_return_pct:+.2f}%\n"
            f"  年化報酬率      : {self.annualized_return_pct:+.2f}%\n"
            f"  年化波動率      : {self.annualized_volatility_pct:.2f}%\n"
            f"  夏普比率        : {self.sharpe_ratio:.3f}\n"
            f"  最大回撤        : {self.max_drawdown_pct:.2f}%\n"
            f"  勝率            : {self.win_rate_pct:.1f}%\n"
            f"  交易次數        : {self.total_trades}\n"
            f"  基準 (SPY) 報酬 : {self.benchmark_return_pct:+.2f}%\n"
            f"  Alpha           : {self.alpha_pct:+.2f}%\n"
        )


class PerformanceMetrics:
    """Compute standard quantitative finance performance metrics."""

    def compute(
        self,
        portfolio_values: pd.Series,
        benchmark_values: pd.Series,
        trades: list[dict],
        risk_free_rate_annual: float = 0.05,
    ) -> PerformanceReport:
        returns = portfolio_values.pct_change().dropna()
        bench_returns = benchmark_values.pct_change().dropna()

        # Total return
        total_return = (portfolio_values.iloc[-1] / portfolio_values.iloc[0] - 1) * 100
        bench_total = (benchmark_values.iloc[-1] / benchmark_values.iloc[0] - 1) * 100

        # Annualized return (CAGR)
        n_years = len(portfolio_values) / TRADING_DAYS_PER_YEAR
        ann_return = ((1 + total_return / 100) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0.0

        # Annualized volatility
        ann_vol = returns.std() * math.sqrt(TRADING_DAYS_PER_YEAR) * 100

        # Sharpe ratio
        excess = returns - risk_free_rate_annual / TRADING_DAYS_PER_YEAR
        sharpe = (excess.mean() / returns.std() * math.sqrt(TRADING_DAYS_PER_YEAR)
                  if returns.std() > 0 else 0.0)

        # Max drawdown
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.cummax()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_dd = drawdown.min() * 100

        # Win rate
        profitable = [t for t in trades if t.get("pnl_pct", 0) > 0]
        win_rate = len(profitable) / len(trades) * 100 if trades else 0.0

        return PerformanceReport(
            total_return_pct=total_return,
            annualized_return_pct=ann_return,
            annualized_volatility_pct=ann_vol,
            sharpe_ratio=sharpe,
            max_drawdown_pct=max_dd,
            win_rate_pct=win_rate,
            total_trades=len(trades),
            profitable_trades=len(profitable),
            benchmark_return_pct=bench_total,
            alpha_pct=total_return - bench_total,
        )
