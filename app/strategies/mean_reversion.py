"""전략 3. 평균회귀 과매도 반등 전략"""

from __future__ import annotations

import pandas as pd

from app.core.types import AccountState, OrderRequest, OrderSide, OrderType, Signal, SignalAction
from app.market.indicators import TechnicalIndicators as TI

from .base import Strategy
from .registry import StrategyRegistry


@StrategyRegistry.register
class MeanReversion(Strategy):
    name = "mean_reversion"
    timeframe = "5m"
    warmup_bars = 40
    max_positions = 5
    supports_overnight = False

    def __init__(self, rsi_period: int = 2, rsi_threshold: float = 10.0,
                 stop_loss_pct: float = 2.0, take_profit_pct: float = 3.0):
        self.rsi_period = rsi_period
        self.rsi_threshold = rsi_threshold
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def prepare_features(self, bars: pd.DataFrame) -> pd.DataFrame:
        bars = bars.copy()
        bars["rsi_short"] = TI.rsi(bars["close"], self.rsi_period)
        bars["sma_20"] = TI.sma(bars["close"], 20)
        bars["pct_change_5"] = bars["close"].pct_change(5) * 100
        return bars

    def on_bar(self, current_time, data_slice: pd.DataFrame, positions: list, account_state: AccountState) -> list[Signal]:
        if len(data_slice) < self.warmup_bars:
            return []

        signals = []
        last = data_slice.iloc[-1]
        held_codes = {p.stock_code for p in positions}
        stock_code = last.get("stock_code", "")

        if stock_code and stock_code not in held_codes:
            oversold = last["rsi_short"] < self.rsi_threshold
            recent_drop = last["pct_change_5"] < -5.0
            has_volume = last.get("volume", 0) > 0

            if oversold and recent_drop and has_volume:
                signals.append(
                    Signal(
                        stock_code=stock_code,
                        action=SignalAction.ENTRY,
                        side=OrderSide.BUY,
                        reason=f"과매도 반등: RSI({self.rsi_period})={last['rsi_short']:.1f}, 5일 낙폭={last['pct_change_5']:.1f}%",
                        score=100 - last["rsi_short"],
                        strategy_name=self.name,
                    )
                )

        for pos in positions:
            if pos.strategy_name != self.name:
                continue
            if pos.unrealized_pnl_pct <= -self.stop_loss_pct:
                signals.append(Signal(stock_code=pos.stock_code, action=SignalAction.EXIT, side=OrderSide.SELL,
                                      reason=f"손절 {pos.unrealized_pnl_pct:.1f}%", strategy_name=self.name))
            elif pos.unrealized_pnl_pct >= self.take_profit_pct:
                signals.append(Signal(stock_code=pos.stock_code, action=SignalAction.EXIT, side=OrderSide.SELL,
                                      reason=f"익절 {pos.unrealized_pnl_pct:.1f}%", strategy_name=self.name))

        return signals

    def generate_orders(self, signals: list[Signal], positions: list, account_state: AccountState) -> list[OrderRequest]:
        orders = []
        for sig in signals:
            if sig.action == SignalAction.ENTRY:
                orders.append(OrderRequest(stock_code=sig.stock_code, stock_name="", side=OrderSide.BUY,
                                           order_type=OrderType.LIMIT, qty=0, strategy_name=self.name, reason=sig.reason))
            elif sig.action == SignalAction.EXIT:
                pos = next((p for p in positions if p.stock_code == sig.stock_code), None)
                if pos:
                    orders.append(OrderRequest(stock_code=sig.stock_code, stock_name=pos.stock_name, side=OrderSide.SELL,
                                               order_type=OrderType.MARKET, qty=pos.qty, strategy_name=self.name, reason=sig.reason))
        return orders
