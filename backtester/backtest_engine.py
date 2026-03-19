"""Event-driven backtesting engine.

Strategy logic:
  - When a bearish signal fires → reduce equity holdings (sell a portion)
  - When a bullish signal fires → increase equity holdings (buy)
  - Positions are closed after a configurable holding period
  - Portfolio is benchmarked against SPY buy-and-hold
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

from config import BACKTEST_YEARS, INITIAL_CAPITAL, SECTOR_TICKERS
from backtester.performance_metrics import PerformanceMetrics, PerformanceReport
from ai_analyzer.strategy_generator import InvestmentStrategy

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    years: int = BACKTEST_YEARS
    initial_capital: float = INITIAL_CAPITAL
    transaction_cost_pct: float = 0.001   # 0.1% per trade
    holding_days: int = 20                # default position hold period
    max_position_pct: float = 0.30        # max 30% in any single asset


@dataclass
class Trade:
    ticker: str
    action: str             # BUY / SELL / SHORT
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    shares: float
    pnl_pct: float
    capital_used: float


@dataclass
class BacktestResult:
    strategy_name: str
    config: BacktestConfig
    performance: PerformanceReport
    trades: list[Trade]
    portfolio_values: pd.Series
    benchmark_values: pd.Series

    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"策略: {self.strategy_name}")
        print(f"{'='*60}")
        print(self.performance.summary_str())


class BacktestEngine:
    """Simulates event-driven investment strategies on historical data."""

    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()
        self.metrics = PerformanceMetrics()

    def run(
        self,
        strategy: InvestmentStrategy,
        strategy_name: str = "AI Signal Strategy",
    ) -> BacktestResult:
        """Run backtest for a given InvestmentStrategy over historical data."""
        end_date = datetime.today()
        start_date = end_date - timedelta(days=self.config.years * 365)

        # Gather unique tickers from strategy actions
        tickers = list({a.asset for a in strategy.actions if self._looks_like_ticker(a.asset)})
        if not tickers:
            # Fall back to first available sector tickers
            tickers = SECTOR_TICKERS.get("technology", ["AAPL", "MSFT"])

        # Download price data
        prices = self._download_prices(tickers, start_date, end_date)
        benchmark = self._download_prices(["SPY"], start_date, end_date)

        if prices.empty or benchmark.empty:
            logger.warning("Could not download market data; returning empty result.")
            dummy = pd.Series([self.config.initial_capital], index=[pd.Timestamp.today()])
            dummy_bench = pd.Series([self.config.initial_capital], index=[pd.Timestamp.today()])
            return BacktestResult(
                strategy_name=strategy_name,
                config=self.config,
                performance=self.metrics.compute(dummy, dummy_bench, []),
                trades=[],
                portfolio_values=dummy,
                benchmark_values=dummy_bench,
            )

        # Simulate event-driven entries at regular intervals (monthly rebalance)
        trades, portfolio_values = self._simulate(strategy, prices)

        # Scale benchmark to same initial capital
        bench_series = benchmark.iloc[:, 0]
        bench_scaled = bench_series / bench_series.iloc[0] * self.config.initial_capital

        # Align index
        portfolio_values, bench_scaled = portfolio_values.align(bench_scaled, join="inner")

        performance = self.metrics.compute(
            portfolio_values,
            bench_scaled,
            [t.__dict__ for t in trades],
        )

        return BacktestResult(
            strategy_name=strategy_name,
            config=self.config,
            performance=performance,
            trades=trades,
            portfolio_values=portfolio_values,
            benchmark_values=bench_scaled,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _download_prices(
        self, tickers: list[str], start: datetime, end: datetime
    ) -> pd.DataFrame:
        try:
            data = yf.download(
                tickers,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                auto_adjust=True,
                progress=False,
            )
            if isinstance(data.columns, pd.MultiIndex):
                close = data["Close"]
            else:
                close = data[["Close"]] if "Close" in data.columns else data
            return close.dropna(how="all")
        except Exception as exc:
            logger.error("Price download failed: %s", exc)
            return pd.DataFrame()

    def _simulate(
        self, strategy: InvestmentStrategy, prices: pd.DataFrame
    ) -> tuple[list[Trade], pd.Series]:
        """Simple monthly rebalance simulation based on strategy stance."""
        capital = self.config.initial_capital
        portfolio_values: list[tuple] = []
        trades: list[Trade] = []
        dates = prices.index

        # Decide direction from overall stance
        stance = strategy.overall_stance  # bullish / bearish / neutral / defensive
        equity_fraction = {"bullish": 0.90, "neutral": 0.60, "defensive": 0.30, "bearish": 0.20}.get(
            stance, 0.60
        )

        # Use available tickers from prices
        available = [c for c in prices.columns if isinstance(c, str)]
        if not available:
            available = list(prices.columns)

        # Equal-weight among chosen tickers
        weight_per = equity_fraction / len(available) if available else 0

        # Track positions: {ticker: (shares, entry_price, entry_date)}
        positions: dict = {}
        cash = capital

        rebalance_dates = pd.date_range(dates[0], dates[-1], freq="MS")  # monthly start

        for rb_date in rebalance_dates:
            # Find nearest actual trading day
            mask = prices.index >= rb_date
            if not mask.any():
                continue
            trade_date = prices.index[mask][0]

            # Close existing positions
            for ticker, (shares, entry_price, entry_date) in list(positions.items()):
                if ticker not in prices.columns:
                    continue
                exit_price = prices.loc[trade_date, ticker]
                if pd.isna(exit_price):
                    continue
                proceeds = shares * exit_price * (1 - self.config.transaction_cost_pct)
                cost_basis = shares * entry_price
                pnl_pct = (exit_price - entry_price) / entry_price * 100
                cash += proceeds
                trades.append(
                    Trade(
                        ticker=ticker,
                        action="SELL",
                        entry_date=str(entry_date.date()),
                        exit_date=str(trade_date.date()),
                        entry_price=round(entry_price, 4),
                        exit_price=round(exit_price, 4),
                        shares=round(shares, 4),
                        pnl_pct=round(pnl_pct, 4),
                        capital_used=round(cost_basis, 2),
                    )
                )
            positions.clear()

            # Open new positions
            invest_per_ticker = cash * weight_per
            for ticker in available:
                if ticker not in prices.columns:
                    continue
                price = prices.loc[trade_date, ticker]
                if pd.isna(price) or price <= 0:
                    continue
                cost = invest_per_ticker * (1 + self.config.transaction_cost_pct)
                if cost > cash:
                    continue
                shares = invest_per_ticker / price
                cash -= cost
                positions[ticker] = (shares, price, trade_date)

            # Mark-to-market portfolio value
            equity = sum(
                shares * prices.loc[trade_date, t]
                for t, (shares, _, __) in positions.items()
                if t in prices.columns and not pd.isna(prices.loc[trade_date, t])
            )
            portfolio_values.append((trade_date, cash + equity))

        # Final mark-to-market on last available date
        last_date = dates[-1]
        equity = sum(
            shares * prices.loc[last_date, t]
            for t, (shares, _, __) in positions.items()
            if t in prices.columns and not pd.isna(prices.loc[last_date, t])
        )
        portfolio_values.append((last_date, cash + equity))

        ts = pd.Series(
            [v for _, v in portfolio_values],
            index=pd.DatetimeIndex([d for d, _ in portfolio_values]),
        ).sort_index()
        ts = ts[~ts.index.duplicated(keep="last")]
        return trades, ts

    @staticmethod
    def _looks_like_ticker(s: str) -> bool:
        """Heuristic: tickers are 1-5 uppercase letters."""
        return bool(s) and s.isupper() and 1 <= len(s) <= 5 and s.isalpha()
