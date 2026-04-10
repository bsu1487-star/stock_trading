"""백테스트 메인 엔진"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

from app.core.types import AccountState, OrderSide, Position, SignalAction
from app.monitoring.logger import get_logger
from app.simulation.cost_model import CostModel
from app.strategies.base import Strategy

from .resampler import BarResampler

log = get_logger("backtest.engine")


@dataclass
class BacktestTrade:
    stock_code: str
    strategy_name: str
    side: str
    entry_time: pd.Timestamp | None = None
    exit_time: pd.Timestamp | None = None
    entry_price: float = 0.0
    exit_price: float = 0.0
    qty: int = 0
    pnl: float = 0.0
    commission: float = 0.0
    tax: float = 0.0


@dataclass
class BacktestResult:
    initial_cash: float
    final_equity: float
    total_return_pct: float
    trades: list[BacktestTrade] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)

    @property
    def total_trades(self) -> int:
        return len([t for t in self.trades if t.exit_time is not None])

    @property
    def win_rate(self) -> float:
        closed = [t for t in self.trades if t.exit_time is not None]
        if not closed:
            return 0.0
        wins = len([t for t in closed if t.pnl > 0])
        return wins / len(closed) * 100

    @property
    def profit_factor(self) -> float:
        closed = [t for t in self.trades if t.exit_time is not None]
        gross_profit = sum(t.pnl for t in closed if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in closed if t.pnl < 0))
        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0
        return gross_profit / gross_loss

    @property
    def mdd_pct(self) -> float:
        if not self.equity_curve:
            return 0.0
        equities = [e["equity"] for e in self.equity_curve]
        peak = equities[0]
        max_dd = 0.0
        for eq in equities:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return max_dd


class BacktestEngine:
    """분봉 기반 이벤트 재생 백테스트 엔진"""

    def __init__(
        self,
        strategy: Strategy,
        initial_cash: float = 20_000_000,
        cost_model: CostModel | None = None,
        max_positions: int = 5,
        per_stock_weight_pct: float = 15.0,
    ):
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.cost_model = cost_model or CostModel()
        self.max_positions = max_positions
        self.per_stock_weight_pct = per_stock_weight_pct

    def run(self, bars_by_code: dict[str, pd.DataFrame]) -> BacktestResult:
        """
        백테스트 실행.

        Args:
            bars_by_code: {종목코드: 분봉 DataFrame} (datetime, open, high, low, close, volume)
        """
        cash = self.initial_cash
        positions: dict[str, BacktestTrade] = {}
        closed_trades: list[BacktestTrade] = []
        equity_curve: list[dict] = []

        # 리샘플링
        interval = int(self.strategy.timeframe.replace("m", ""))
        resampled: dict[str, pd.DataFrame] = {}
        for code, bars in bars_by_code.items():
            r = BarResampler.resample(bars, interval)
            r["stock_code"] = code
            r = self.strategy.prepare_features(r)
            resampled[code] = r

        # 모든 종목의 시간 합치기
        all_times = set()
        for df in resampled.values():
            dt_col = "datetime" if "datetime" in df.columns else df.index.name
            if dt_col and dt_col in df.columns:
                all_times.update(df[dt_col].tolist())
        all_times = sorted(all_times)

        for t in all_times:
            # 각 종목에 대해 시그널 생성
            for code, df in resampled.items():
                dt_col = "datetime" if "datetime" in df.columns else None
                if dt_col:
                    mask = df[dt_col] <= t
                else:
                    continue

                data_slice = df[mask].tail(self.strategy.warmup_bars + 10)
                if len(data_slice) < self.strategy.warmup_bars:
                    continue

                current_bar = data_slice.iloc[-1]
                prev_bar = data_slice.iloc[-2] if len(data_slice) >= 2 else current_bar
                current_price = float(current_bar["close"])

                # 포지션을 Position 객체로 변환
                pos_list = []
                for pc, trade in positions.items():
                    pos_list.append(
                        Position(pc, "", trade.strategy_name, trade.qty, trade.entry_price, current_price)
                    )

                account = AccountState(
                    total_equity=cash + sum(t.qty * current_price for t in positions.values()),
                    available_cash=cash,
                )

                signals = self.strategy.on_bar(t, data_slice, pos_list, account)

                for sig in signals:
                    if sig.stock_code != code:
                        continue

                    next_price = float(current_bar["open"])  # 보수적: 현재 봉 시가

                    if sig.action == SignalAction.ENTRY and sig.side == OrderSide.BUY:
                        if code in positions:
                            continue
                        if len(positions) >= self.max_positions:
                            continue

                        budget = cash * (self.per_stock_weight_pct / 100)
                        fill_price, commission = self.cost_model.apply_buy(next_price, 1)
                        qty = int(budget / fill_price)
                        if qty <= 0:
                            continue

                        cost = fill_price * qty + commission
                        if cost > cash:
                            continue

                        cash -= cost
                        positions[code] = BacktestTrade(
                            stock_code=code,
                            strategy_name=self.strategy.name,
                            side="buy",
                            entry_time=t,
                            entry_price=fill_price,
                            qty=qty,
                            commission=commission,
                        )

                    elif sig.action == SignalAction.EXIT and code in positions:
                        trade = positions.pop(code)
                        fill_price, commission, tax = self.cost_model.apply_sell(next_price, trade.qty)
                        proceeds = fill_price * trade.qty - commission - tax
                        cash += proceeds

                        trade.exit_time = t
                        trade.exit_price = fill_price
                        trade.pnl = (fill_price - trade.entry_price) * trade.qty - trade.commission - commission - tax
                        trade.commission += commission
                        trade.tax = tax
                        closed_trades.append(trade)

            # 일별 equity
            market_value = sum(
                float(resampled[code][resampled[code]["datetime"] <= t].iloc[-1]["close"]) * trade.qty
                for code, trade in positions.items()
                if len(resampled[code][resampled[code]["datetime"] <= t]) > 0
            )
            equity_curve.append({"datetime": t, "equity": cash + market_value})

        # 미청산 포지션 평가
        final_market_value = 0.0
        for code, trade in positions.items():
            df = resampled[code]
            if len(df) > 0:
                last_price = float(df.iloc[-1]["close"])
                final_market_value += last_price * trade.qty

        final_equity = cash + final_market_value
        total_return_pct = (final_equity - self.initial_cash) / self.initial_cash * 100

        return BacktestResult(
            initial_cash=self.initial_cash,
            final_equity=final_equity,
            total_return_pct=total_return_pct,
            trades=closed_trades,
            equity_curve=equity_curve,
        )
