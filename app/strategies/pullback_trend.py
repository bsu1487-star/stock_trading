"""전략 2. 눌림목 추세추종 전략"""

from __future__ import annotations

import pandas as pd

from app.core.types import AccountState, OrderRequest, OrderSide, OrderType, Signal, SignalAction
from app.market.indicators import TechnicalIndicators as TI

from .base import Strategy
from .registry import StrategyRegistry


@StrategyRegistry.register
class PullbackTrend(Strategy):
    name = "pullback_trend"
    timeframe = "10m"
    warmup_bars = 60
    max_positions = 5
    supports_overnight = True

    def __init__(self, stop_loss_pct: float = 3.0):
        self.stop_loss_pct = stop_loss_pct

    def prepare_features(self, bars: pd.DataFrame) -> pd.DataFrame:
        bars = bars.copy()
        bars["sma_20"] = TI.sma(bars["close"], 20)
        bars["sma_60"] = TI.sma(bars["close"], 60)
        bars["sma_5"] = TI.sma(bars["close"], 5)
        bars["vol_ratio"] = TI.volume_ratio(bars["volume"], 20)
        bars["rsi_14"] = TI.rsi(bars["close"], 14)
        bars["highest_60"] = TI.highest(bars["high"], 60)
        return bars

    def on_bar(self, current_time, data_slice: pd.DataFrame, positions: list, account_state: AccountState) -> list[Signal]:
        if len(data_slice) < self.warmup_bars:
            return []

        signals = []
        last = data_slice.iloc[-1]
        held_codes = {p.stock_code for p in positions}
        stock_code = last.get("stock_code", "")

        if stock_code and stock_code not in held_codes:
            # 중기 상승 추세: 20일선 > 60일선
            trend_up = last["sma_20"] > last["sma_60"]
            # 최근 고가 근처 이력
            near_high = last["close"] > last["highest_60"] * 0.9
            # 단기 조정 후 반등: RSI가 과매도 영역에서 벗어남
            pullback_recovery = 30 < last["rsi_14"] < 50
            # 5일선 회복
            ma5_recovery = last["close"] > last["sma_5"]
            # 거래량 감소 후 재증가
            vol_moderate = last["vol_ratio"] < 1.5

            if trend_up and near_high and pullback_recovery and ma5_recovery:
                signals.append(
                    Signal(
                        stock_code=stock_code,
                        action=SignalAction.ENTRY,
                        side=OrderSide.BUY,
                        reason="눌림목 반등: 추세 상승 + RSI 회복 + 5일선 회복",
                        score=50 + last["rsi_14"],
                        strategy_name=self.name,
                    )
                )

        # 청산
        for pos in positions:
            if pos.strategy_name != self.name:
                continue
            if pos.unrealized_pnl_pct <= -self.stop_loss_pct:
                signals.append(
                    Signal(stock_code=pos.stock_code, action=SignalAction.EXIT, side=OrderSide.SELL,
                           reason=f"손절 {pos.unrealized_pnl_pct:.1f}%", strategy_name=self.name))
            elif last.get("close", 0) < last.get("sma_20", 0):
                signals.append(
                    Signal(stock_code=pos.stock_code, action=SignalAction.EXIT, side=OrderSide.SELL,
                           reason="20일선 이탈", strategy_name=self.name))

        return signals

    def generate_orders(self, signals: list[Signal], positions: list, account_state: AccountState) -> list[OrderRequest]:
        orders = []
        for sig in signals:
            if sig.action == SignalAction.ENTRY:
                orders.append(OrderRequest(stock_code=sig.stock_code, stock_name="", side=OrderSide.BUY,
                                           order_type=OrderType.MARKET, qty=0, strategy_name=self.name, reason=sig.reason))
            elif sig.action == SignalAction.EXIT:
                pos = next((p for p in positions if p.stock_code == sig.stock_code), None)
                if pos:
                    orders.append(OrderRequest(stock_code=sig.stock_code, stock_name=pos.stock_name, side=OrderSide.SELL,
                                               order_type=OrderType.MARKET, qty=pos.qty, strategy_name=self.name, reason=sig.reason))
        return orders
