"""전략 1. 단기 모멘텀 돌파 전략"""

from __future__ import annotations

import pandas as pd

from app.core.types import AccountState, OrderRequest, OrderSide, OrderType, Signal, SignalAction
from app.market.indicators import TechnicalIndicators as TI

from .base import Strategy
from .registry import StrategyRegistry


@StrategyRegistry.register
class MomentumBreakout(Strategy):
    name = "momentum_breakout"
    timeframe = "5m"
    warmup_bars = 80
    max_positions = 5
    supports_overnight = False

    def __init__(self, breakout_period: int = 20, stop_loss_pct: float = 3.0, take_profit_pct: float = 5.0):
        self.breakout_period = breakout_period
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def prepare_features(self, bars: pd.DataFrame) -> pd.DataFrame:
        bars = bars.copy()
        bars["highest_n"] = TI.highest(bars["high"], self.breakout_period)
        bars["vol_ratio"] = TI.volume_ratio(bars["volume"], 20)
        bars["sma_20"] = TI.sma(bars["close"], 20)
        return bars

    def on_bar(self, current_time, data_slice: pd.DataFrame, positions: list, account_state: AccountState) -> list[Signal]:
        if len(data_slice) < self.warmup_bars:
            return []

        signals = []
        last = data_slice.iloc[-1]
        prev = data_slice.iloc[-2]

        held_codes = {p.stock_code for p in positions}

        # 진입: 직전 N봉 고가 돌파 + 거래량 급증
        stock_code = last.get("stock_code", "")
        if stock_code and stock_code not in held_codes:
            if last["close"] > prev["highest_n"] and last["vol_ratio"] > 2.0:
                signals.append(
                    Signal(
                        stock_code=stock_code,
                        action=SignalAction.ENTRY,
                        side=OrderSide.BUY,
                        reason=f"{self.breakout_period}봉 고가 돌파, 거래량 {last['vol_ratio']:.1f}배",
                        score=last["vol_ratio"] * 10,
                        stop_price=last["close"] * (1 - self.stop_loss_pct / 100),
                        target_price=last["close"] * (1 + self.take_profit_pct / 100),
                        strategy_name=self.name,
                    )
                )

        # 청산: 보유 종목 손절/익절
        for pos in positions:
            if pos.strategy_name != self.name:
                continue
            if pos.unrealized_pnl_pct <= -self.stop_loss_pct:
                signals.append(
                    Signal(
                        stock_code=pos.stock_code,
                        action=SignalAction.EXIT,
                        side=OrderSide.SELL,
                        reason=f"손절 {pos.unrealized_pnl_pct:.1f}%",
                        strategy_name=self.name,
                    )
                )
            elif pos.unrealized_pnl_pct >= self.take_profit_pct:
                signals.append(
                    Signal(
                        stock_code=pos.stock_code,
                        action=SignalAction.EXIT,
                        side=OrderSide.SELL,
                        reason=f"익절 {pos.unrealized_pnl_pct:.1f}%",
                        strategy_name=self.name,
                    )
                )

        return signals

    def generate_orders(self, signals: list[Signal], positions: list, account_state: AccountState) -> list[OrderRequest]:
        orders = []
        for sig in signals:
            if sig.action == SignalAction.ENTRY:
                orders.append(
                    OrderRequest(
                        stock_code=sig.stock_code,
                        stock_name="",
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        qty=0,  # sizing은 execution 레이어에서 계산
                        strategy_name=self.name,
                        reason=sig.reason,
                    )
                )
            elif sig.action == SignalAction.EXIT:
                pos = next((p for p in positions if p.stock_code == sig.stock_code), None)
                if pos:
                    orders.append(
                        OrderRequest(
                            stock_code=sig.stock_code,
                            stock_name=pos.stock_name,
                            side=OrderSide.SELL,
                            order_type=OrderType.MARKET,
                            qty=pos.qty,
                            strategy_name=self.name,
                            reason=sig.reason,
                        )
                    )
        return orders
